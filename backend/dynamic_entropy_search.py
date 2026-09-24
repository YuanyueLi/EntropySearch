#!/usr/bin/env python3
import copy
from pathlib import Path

import numpy as np
from ms_entropy import (
    DynamicEntropySearch,
    read_one_spectrum,
    standardize_spectrum,
)

__VERSION__ = "2.0.0"


def worker_search_one_spectrum(function, parameters_global, queue_input, queue_output):
    for parameters in iter(queue_input.get, None):
        try:
            result = function(*parameters, *parameters_global)
            queue_output.put(result)
        except Exception as e:
            print(e)
            queue_output.put(None)


class DynamicEntropy:
    def __init__(self, ms2_tolerance_in_da) -> None:
        self.ms2_tolerance_in_da = ms2_tolerance_in_da
        self.spectral_library = None
        self.all_spectra = []
        self.scan_number_to_index = {}
        self.all_processes = []
        self.queue_input = None
        self.queue_output = None

        # Status
        # 1. When program starts, status is ready: False, running: False, error: False
        # 2. When program starts searching, status is ready: False, running: True, error: False
        # 3. When program finishes reading all spectra, but not all spectra have been searched, status is ready: True, running: True, error: False
        # 4. When program finishes searching all spectra, status is ready: True, running: False, error: False
        # 5. When program finds error, status is ready: False, running: False, error: True
        self.status = {
            "ready": False,  # True means ready to display results, if error found, ready will be False.
            "running": False,  # True means searching is running, False means searching is not running.
            "error": False,  # True means error found
            "message": "",  # Message to display
        }

    def search_one_spectrum(
        self, spec, top_n, ms1_tolerance_in_da, ms2_tolerance_in_da
    ):
        spec = _parse_spectrum(spec)
        result = {
            "scan": spec["scan"],
            "query_name": spec["name"],
            "precursor_mz": spec["precursor_mz"],
            "charge": spec["charge"],
            "rt": spec["rt"],
        }
        if (
            spec["precursor_mz"] <= 0
            or len(spec["peaks"]) == 0
            or spec["charge"] not in self.spectral_library
        ):
            for search_type in [
                "identity_search",
                "open_search",
                "neutral_loss_search",
                "hybrid_search",
            ]:
                result[search_type] = []
                result[search_type + "-score"] = 0
        else:
            entropy_search = self.spectral_library[spec["charge"]]
            entropy_search_result = entropy_search.search(
                precursor_mz=spec["precursor_mz"],
                peaks=spec["peaks"],
                ms1_tolerance_in_da=ms1_tolerance_in_da,
                ms2_tolerance_in_da=ms2_tolerance_in_da,
                method="all",
            )
            for search_type, score_array in entropy_search_result.items():
                # Select top N results
                if top_n < len(score_array):
                    top_n_idx = np.argpartition(score_array, -top_n)[-top_n:]
                    top_n_score = score_array[top_n_idx]
                else:
                    top_n_idx = np.arange(len(score_array))
                    top_n_score = score_array

                # Filter by score > 0
                selected_idx = top_n_score > 0
                top_n_idx = top_n_idx[selected_idx]
                top_n_score = top_n_score[selected_idx]

                # Assign name when search_type is identity_search
                if search_type == "identity_search" and len(top_n_idx) > 0:
                    # Select the max score
                    max_idx = np.argmax(top_n_score)
                    # Get the library spectrum
                    library_spec = entropy_search[top_n_idx[max_idx]]
                    print(library_spec)
                    # Assign name
                    result["name"] = library_spec["library-name"]
                    result["adduct"] = library_spec["library-precursor_type"]

                result[search_type] = [
                    [spec["scan"], i, score_array[i]] for i in top_n_idx
                ]

                if len(top_n_score) > 0:
                    result[search_type + "-score"] = np.max(top_n_score)
                else:
                    result[search_type + "-score"] = 0
        return result

    def get_one_library_spectrum(self, charge, library_idx):
        return self.spectral_library[charge][library_idx]

    def get_one_spectrum_result(
        self, scan_number, top_n, ms1_tolerance_in_da, ms2_tolerance_in_da
    ):
        spec_idx = self.scan_number_to_index[scan_number]
        spectrum_result = None
        spectrum_result = copy.copy(self.all_spectra[spec_idx])
        if self.status["running"]:
            spectrum_result.update(
                self.search_one_spectrum(
                    spectrum_result, top_n, ms1_tolerance_in_da, ms2_tolerance_in_da
                )
            )

        search_type_keys = [
            "identity_search",
            "open_search",
            "neutral_loss_search",
            "hybrid_search",
        ]
        for search_type in search_type_keys:
            new_data = []
            for query_idx, library_idx, score in spectrum_result[search_type]:
                library_spec = self.spectral_library[spectrum_result["charge"]][
                    library_idx
                ]
                new_data.append([library_spec, score])
            spectrum_result[search_type] = new_data

        return spectrum_result

    def stop(self, timeout=None):
        self.status = {
            "ready": False,
            "message": "Stopping...",
            "error": False,
            "running": False,
        }

        # Clear the input queue
        if self.queue_input is not None:
            while not self.queue_input.empty():
                self.queue_input.get()
            # Put None to the input queue
            for _ in range(len(self.all_processes)):
                self.queue_input.put(None)

        # Join all processes
        for p in self.all_processes:
            p.join(timeout)

        # Clear the input queue again
        if self.queue_input is not None:
            while not self.queue_input.empty():
                self.queue_input.get()
        self.queue_input.close()
        self.queue_input = None

        self.queue_output.close()
        self.queue_output = None

        self.status = {
            "ready": False,
            "message": "Stopping...",
            "error": False,
            "running": False,
        }

    def exit(self):
        self.stop(0.1)
        # Kill all processes
        for p in self.all_processes:
            try:
                p.kill()
                p.join()
            except:
                pass
        self.all_processes = []

    def search_file_single_core(
        self,
        file_query,
        top_n,
        ms1_tolerance_in_da,
        ms2_tolerance_in_da,
        charge=None,
        cores=1,
    ):
        # Search spectra
        file_query = Path(file_query)
        all_results = []
        self.status = {
            "ready": False,
            "running": True,
            "error": False,
            "message": f"Start reading {file_query.name}...",
        }
        for spec_num, spec in enumerate(read_one_spectrum(file_query)):
            if spec_num % 100 == 0:
                self.status["message"] = (
                    f"Reading {file_query.name}... {spec_num} spectra read"
                )
                print(f"Reading {file_query.name}... {spec_num} spectra read")
            if spec.pop("_ms_level", 2) != 2:
                continue
            spec["charge"] = 0
            # if charge is not None:
            #     spec["charge"] = charge
            spec["peaks"] = np.array(spec["peaks"]).astype(np.float32)
            self.all_spectra.append(spec)
            self.scan_number_to_index[spec["_scan_number"]] = len(self.all_spectra) - 1

            # if spec.pop("_ms_level", 2) != 2:
            #     continue
            # spec['peaks'] = np.array(spec['peaks']).astype(np.float32)

            cur_result = self.search_one_spectrum(
                spec, top_n, ms1_tolerance_in_da, ms2_tolerance_in_da
            )
            if cur_result is not None:
                spec_idx = self.scan_number_to_index[cur_result["scan"]]
                self.all_spectra[spec_idx].update(cur_result)
            # all_results.append(result)
            # # if len(all_results) > 100:
            # #     break

        self.status = {
            "ready": True,
            "running": False,
            "error": False,
            "message": f"",
        }
        return all_results

    def load_spectral_library(self, file_library) -> None:
        file_library = Path(file_library)
        if not (file_library / "group_start.pkl").exists():
            self.status = {
                "ready": False,
                "running": False,
                "error": True,
                "message": f"{file_library} does not look like a prebuilt DynamicEntropySearch index.",
            }
            return
        self.status = {
            "ready": False,
            "running": True,
            "error": False,
            "message": f"Loading index from {file_library}...",
        }
        self.spectral_library = DynamicEntropySearch(
            path_data=file_library, max_ms2_tolerance_in_da=self.ms2_tolerance_in_da
        )
        self.status = {"ready": True, "running": False, "error": False, "message": ""}


def _parse_spectrum(spec):
    def convert_float(x):
        try:
            f = float(x)
            if np.isnan(f):
                return -1
            else:
                return f
        except:
            return -1

    def convert_precursor_mz(x):
        try:
            f = float(x)
            if np.isnan(f):
                return -1
            else:
                return f
        except:
            try:
                return float(x.split()[0])
            except:
                return -1

    spec = standardize_spectrum(
        spec,
        standardize_info={
            "id": [["db#"], "", str],
            "scan": [["_scan_number"], -1, int],
            "name": [["title"], "", str],
            "rt": [["retentiontime"], -1, convert_float],
            "precursor_mz": [["precursormz", "pepmass"], -1, convert_precursor_mz],
            "ion_mode": [["ionmode"], "", str],
            "precursor_type": [["precursortype"], "", str],
            "charge": [[], "", str],
            "name": [["title"], "", str],
        },
    )

    charge = 0

    spec["charge"] = charge
    return spec


if __name__ == "__main__":
    para = {
        "ms1_tolerance_in_da": 0.01,
        "ms2_tolerance_in_da": 0.02,
        "top_n": 10,
        "cores": 1,
        "file_query": r"/p/github/EntropySearch/test/test_2.mzML",
        # "file_library": r"/p/github/EntropySearch/test/MoNA-export-All_Spectra.msp",
        # "file_query": r"/p/FastEntropySearch/gui/test/input/test.mgf",
        "file_library": r"/p/FastEntropySearch/gui/test/input/test.mgf",
        "file_output": r"/p/github/EntropySearch/test/result.csv",
    }
    entropy_search = EntropySearch(para["ms2_tolerance_in_da"])
    entropy_search.load_spectral_library(Path(para["file_library"]))
    all_results = entropy_search.search_file_single_core(
        Path(para["file_query"]),
        para["top_n"],
        para["ms1_tolerance_in_da"],
        para["ms2_tolerance_in_da"],
        cores=para["cores"],
    )
    a = 1
    # test = entropy_search.get_one_spectrum_result(5, para["top_n"], para["ms1_tolerance_in_da"], para["ms2_tolerance_in_da"])
    # print(test)
    # test2 = entropy_search.get_one_library_spectrum(charge=1, library_idx=1489)
    # print(test2)
