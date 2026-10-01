#!/usr/bin/env python3
import copy
import hashlib
import json
import pickle
from pathlib import Path

import numpy as np
from ms_entropy import (
    DynamicEntropySearch,
    FlashEntropySearch,
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


class EntropySearch:
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
            or self.spectral_library is None
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
            entropy_search_result = self.spectral_library.search(
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
                    library_spec = self.spectral_library[top_n_idx[max_idx]]
                    # Assign name
                    result["name"] = library_spec.get("library-name", "")
                    result["adduct"] = library_spec.get("library-precursor_type", "")

                result[search_type] = [
                    [spec["scan"], i, score_array[i]] for i in top_n_idx
                ]

                if len(top_n_score) > 0:
                    result[search_type + "-score"] = np.max(top_n_score)
                else:
                    result[search_type + "-score"] = 0
        return result

    def get_one_library_spectrum(self, library_idx):
        return self.spectral_library[library_idx]

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
                # Load the library spec, without the peaks (to sent a bit lighter data), peak data is later loaded using main.get_one_spectrum, which calls get_one_library_spectrum, which includes the peaks
                library_spec = {
                    k: v
                    for k, v in self.spectral_library[library_idx].items()
                    if k != "peaks"
                }
                library_spec["library-idx"] = int(library_idx)
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
            try:
                if spec_num % 100 == 0:
                    self.status["message"] = (
                        f"Reading {file_query.name}... {spec_num} spectra read"
                    )
                if spec.pop("_ms_level", 2) != 2:
                    continue

                spec["peaks"] = np.array(spec["peaks"]).astype(np.float32)
                self.all_spectra.append(spec)
                self.scan_number_to_index[spec["_scan_number"]] = (
                    len(self.all_spectra) - 1
                )

                cur_result = self.search_one_spectrum(
                    spec, top_n, ms1_tolerance_in_da, ms2_tolerance_in_da
                )
                if cur_result is not None:
                    spec_idx = self.scan_number_to_index[cur_result["scan"]]
                    self.all_spectra[spec_idx].update(cur_result)
            except Exception as e:
                continue

        self.status = {
            "ready": True,
            "running": False,
            "error": False,
            "message": f"",
        }
        return all_results

    def load_spectral_library(self, file_library) -> None:
        file_library = Path(file_library)
        self.status = {
            "ready": False,
            "running": True,
            "error": False,
            "message": "Start loading spectral library...",
        }
        if file_library.name == "group_start.pkl":
            file_library = file_library.parent
            self.spectral_library = DynamicEntropySearch(
                path_data=file_library, max_ms2_tolerance_in_da=self.ms2_tolerance_in_da
            )
        else:
            self.status["message"] = f"Loading {file_library.name}..."
            # Check if the library is already indexed
            self._build_spectral_library(file_library)

    def _build_spectral_library(self, file_library):
        # Calculate hash of file_library
        index_hash = hashlib.md5(
            json.dumps(
                {
                    "ms2_tolerance_in_da": self.ms2_tolerance_in_da,
                    "version": __VERSION__,
                }
            ).encode()
        ).hexdigest()[:6]

        # Check if the library is already indexed
        if file_library.suffix == ".esi":
            try:
                with open(file_library, "rb") as f:
                    self.spectral_library = pickle.load(f)
                return True
            except:
                pass

        # Check if the library is existed
        file_library_index = file_library.parent / (
            file_library.name + "." + index_hash + ".esi"
        )
        library_name = ".".join(file_library_index.stem.split(".")[:-2])
        if file_library_index.exists():
            try:
                with open(file_library_index, "rb") as f:
                    self.spectral_library = pickle.load(f)
                return True
            except:
                pass
        # todo make separate function
        library_spectra = []
        spectral_number = 0
        # Read spectra
        for spec in read_one_spectrum(file_library):
            try:
                # spec_raw = spec
                spec["peaks"] = np.array(spec["peaks"]).astype(np.float32)
                spec = _parse_spectrum(spec)

                if (
                    spec["precursor_mz"] <= 0
                    or len(spec["peaks"]) == 0
                    or spec.get("_ms_level", 2) != 2
                ):
                    continue

                all_spec_keys = list(spec.keys())
                all_spec_keys.remove("peaks")
                all_spec_keys.remove("precursor_mz")
                all_spec_keys.remove("_ms_level")
                for k in all_spec_keys:
                    spec["library-" + k] = spec.pop(k)
                spec["library-file_name"] = library_name

                library_spectra.append(spec)
                spectral_number += 1

                if spectral_number % 1000 == 0:
                    self.status["message"] = (
                        f"Loading {spectral_number} spectra from {library_name}..."
                    )
            except:
                continue

        # Build index
        self.status["message"] = (
            f"Building index for {library_name}, this may take up to 10 minutes depending on the size of the library..."
        )
        self.spectral_library = FlashEntropySearch(
            max_ms2_tolerance_in_da=self.ms2_tolerance_in_da
        )
        self.spectral_library.build_index(
            all_spectra_list=library_spectra,
            min_ms2_difference_in_da=2 * self.ms2_tolerance_in_da,
        )
        self.status["message"] = f"Saving index for {library_name}..."
        # Save index
        with open(file_library_index, "wb") as f:
            pickle.dump(self.spectral_library, f)
        return True


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
            "rt": [["retentiontime", "RTINSECONDS", "rtinseconds"], -1, convert_float],
            "precursor_mz": [["precursormz", "pepmass"], -1, convert_precursor_mz],
            "ion_mode": [["ionmode"], "", str],
            "precursor_type": [["precursortype"], "", str],
            "charge": [[], "", str],
            "name": [["title"], "", str],
        },
    )
    return spec


if __name__ == "__main__":
    para = {
        "ms1_tolerance_in_da": 0.01,
        "ms2_tolerance_in_da": 0.02,
        "top_n": 10,
        "cores": 1,
        "file_query": r"C:\Users\jonge094\Repos\kb_aihrms\data\example_files\DDA_and_DIA\a_few_spectra.mgf",
        "file_library": r"C:\Users\jonge094\Repos\kb_aihrms\data\example_files\DDA_and_DIA\a_few_spectra.mgf",
    }
    dynamic_entropy = EntropySearch(para["ms2_tolerance_in_da"])
    dynamic_entropy.load_spectral_library(Path(para["file_library"]))
    all_results = dynamic_entropy.search_file_single_core(
        Path(para["file_query"]),
        para["top_n"],
        para["ms1_tolerance_in_da"],
        para["ms2_tolerance_in_da"],
    )
    print(dynamic_entropy.all_spectra)
