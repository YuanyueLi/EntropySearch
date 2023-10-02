#!/usr/bin/env python3
from pathlib import Path
import json
import numpy as np
import base64
import pickle
from ms_entropy import FlashEntropySearch, read_one_spectrum, standardize_spectrum
import multiprocessing as mp
import copy


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
            "message": ""  # Message to display
        }

    def search_one_spectrum(self, spec, top_n, ms1_tolerance_in_da, ms2_tolerance_in_da):
        spec = _parse_spectrum(spec)
        result = {
            "scan": spec["scan"],
            "precursor_mz": spec["precursor_mz"],
            "charge": spec["charge"],
            "rt": spec["rt"],
        }
        if spec["precursor_mz"] <= 0 or \
                len(spec["peaks"]) == 0 or \
                spec["charge"] not in self.spectral_library:
            for search_type in ["identity_search", "open_search", "neutral_loss_search", "hybrid_search"]:
                result[search_type] = []
                result[search_type+"-score"] = 0
        else:
            entropy_search = self.spectral_library[spec["charge"]]
            entropy_search_result = entropy_search.search(
                precursor_mz=spec["precursor_mz"],
                peaks=spec["peaks"],
                ms1_tolerance_in_da=ms1_tolerance_in_da,
                ms2_tolerance_in_da=ms2_tolerance_in_da,
                method="all"
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
                    library_spec = entropy_search.abstract_library_spectra[top_n_idx[max_idx]]
                    # Assign name
                    result["name"] = library_spec["library-name"]
                    result["adduct"] = library_spec["library-precursor_type"]

                result[search_type] = [[spec["scan"], i, score_array[i]] for i in top_n_idx]

                if len(top_n_score) > 0:
                    result[search_type+"-score"] = np.max(top_n_score)
                else:
                    result[search_type+"-score"] = 0
        return result

    def get_one_library_spectrum(self, charge, library_idx):
        return self.spectral_library[charge][library_idx]

    def get_one_spectrum_result(self, scan_number, top_n, ms1_tolerance_in_da, ms2_tolerance_in_da):
        spec_idx = self.scan_number_to_index[scan_number]
        spectrum_result = None
        spectrum_result = copy.copy(self.all_spectra[spec_idx])
        if self.status["running"]:
            spectrum_result.update(self.search_one_spectrum(spectrum_result, top_n, ms1_tolerance_in_da, ms2_tolerance_in_da))

        search_type_keys = ["identity_search", "open_search", "neutral_loss_search", "hybrid_search"]
        for search_type in search_type_keys:
            new_data = []
            for query_idx, library_idx, score in spectrum_result[search_type]:
                library_spec = self.spectral_library[spectrum_result["charge"]].abstract_library_spectra[library_idx]
                new_data.append([library_spec, score])
            spectrum_result[search_type] = new_data

        return spectrum_result

    def search_file(self, file_query, top_n, ms1_tolerance_in_da, ms2_tolerance_in_da, charge=None, cores=2):
        # Search spectra
        all_results = []
        file_query = Path(file_query)
        self.status = {
            "ready": False,
            "running": True,
            "error": False,
            "message": f"Start reading {file_query.name}..."
        }

        try:
            if charge == 0:
                charge = None
            if charge is not None:
                charge = str(charge).strip()
                if charge == "":
                    charge = None
            if cores > 0:
                self.queue_input, self.queue_output = mp.Queue(), mp.Queue()
                queue_input_num = 0

                self.all_processes = [
                    mp.Process(
                        target=worker_search_one_spectrum,
                        args=(self.search_one_spectrum, (top_n, ms1_tolerance_in_da, ms2_tolerance_in_da,),
                              self.queue_input, self.queue_output)) for _ in range(cores)]
                for p in self.all_processes:
                    p.start()

                for spec in read_one_spectrum(file_query):
                    try:
                        if spec.pop("_ms_level", 2) != 2:
                            continue
                        if charge is not None:
                            spec["charge"] = charge
                        spec['peaks'] = np.array(spec['peaks']).astype(np.float32)
                        self.queue_input.put((spec,))
                        self.all_spectra.append(spec)
                        self.scan_number_to_index[spec["_scan_number"]] = len(self.all_spectra) - 1
                        queue_input_num += 1
                    except Exception as e:
                        continue

                    if queue_input_num % 1000 == 0:
                        self.status["message"] = f"Reading {file_query.name}... {queue_input_num} spectra read"

                # Set ready to display results signal
                self.status["ready"] = True
                for _ in range(cores):
                    self.queue_input.put(None)

                total_spec_num = queue_input_num
                while queue_input_num > 0:
                    cur_result = self.queue_output.get()
                    queue_input_num -= 1
                    # Merge results into original file
                    if cur_result is not None:
                        spec_idx = self.scan_number_to_index[cur_result["scan"]]
                        self.all_spectra[spec_idx].update(cur_result)

                    processed_spec_num = total_spec_num - queue_input_num
                    if processed_spec_num % 100 == 0:
                        self.status["message"] = f"{processed_spec_num} spectra searched, about {queue_input_num} remaining"
                        # print(f"Total: {total_spec_num}, Processed: {processed_spec_num}, Remaining: {queue_input_num}")

                for p in self.all_processes:
                    p.join()

                self.all_processes = []

            # Set success finished signal
            self.status = {
                "ready": True,
                "running": False,
                "error": False,
                "message": f"",
            }
            return all_results
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.status = {
                "ready": False,
                "message": f"Error: {e}",
                "error": True,
                "running": False,
            }
            return []

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

    def search_file_single_core(self, file_query, top_n, ms1_tolerance_in_da, ms2_tolerance_in_da, cores=1):
        # Search spectra
        all_results = []
        self.status = {
            "ready": False,
            "running": True,
            "error": False,
            "message": f"Start reading {file_query.name}..."
        }
        for spec_num, spec in enumerate(read_one_spectrum(file_query)):
            try:
                if spec.pop("_ms_level", 2) != 2:
                    continue
                spec['peaks'] = np.array(spec['peaks']).astype(np.float32)

                result = self.search_one_spectrum(spec, top_n, ms1_tolerance_in_da, ms2_tolerance_in_da)
                all_results.append(result)
                # if len(all_results) > 100:
                #     break
                if spec_num % 100 == 0:
                    self.status["message"] = f"Searching {file_query.name}... {spec_num} spectra searched"
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

        self.status["message"] = f"Loading {file_library.name}..."
        # Check if the library is already indexed
        self._build_spectral_library(file_library)

        # Enable support for multiple cores
        for entropy_search in self.spectral_library.values():
            entropy_search.save_memory_for_multiprocessing()

    def _build_spectral_library(self, file_library):
        # Calculate hash of file_library
        index_hash = base64.b64encode(json.dumps({
            "ms2_tolerance_in_da": self.ms2_tolerance_in_da,
            "version": "1.1.0"
        }).encode()).decode()[:6]

        # Check if the library is already indexed
        if file_library.suffix == ".esi":
            try:
                with open(file_library, "rb") as f:
                    self.spectral_library = pickle.load(f)
                return True
            except:
                pass

        # Check if the library is existed
        file_library_index = file_library.parent / (file_library.name + "." + index_hash + ".esi")
        library_name = ".".join(file_library_index.stem.split(".")[:-2])
        if file_library_index.exists():
            try:
                with open(file_library_index, "rb") as f:
                    self.spectral_library = pickle.load(f)
                return True
            except:
                pass

        spectral_library = {}
        spectral_number = 0
        # Read spectra
        for spec in read_one_spectrum(file_library):
            try:
                spec['peaks'] = np.array(spec['peaks']).astype(np.float32)
                spec = _parse_spectrum(spec)

                if spec["precursor_mz"] <= 0 or len(spec["peaks"]) == 0 or spec.get("_ms_level", 2) != 2:
                    continue

                charge = spec["charge"]
                if charge not in spectral_library:
                    spectral_library[charge] = []

                all_spec_keys = list(spec.keys())
                all_spec_keys.remove("peaks")
                all_spec_keys.remove("precursor_mz")
                all_spec_keys.remove("_ms_level")
                for k in all_spec_keys:
                    spec["library-"+k] = spec.pop(k)
                spec["library-file_name"] = library_name

                spectral_library[charge].append(spec)
                spectral_number += 1

                if spectral_number % 1000 == 0:
                    self.status["message"] = f"Loading {spectral_number} spectra from {library_name}..."
            except:
                continue

        # Build index
        self.status["message"] = f"Building index for {library_name}..."
        for charge, spectra in spectral_library.items():
            entropy_search = FlashEntropySearch(max_ms2_tolerance_in_da=self.ms2_tolerance_in_da)
            all_library_spectra = entropy_search.build_index(all_spectra_list=spectra, min_ms2_difference_in_da=2*self.ms2_tolerance_in_da)
            # Generate abstract spectra information
            all_library_spectra_abstract = []
            for spec in all_library_spectra:
                spec_abstract = {
                    "library-id": spec.get("library-id", spec.get("library-scan", "")),
                    "precursor_mz": spec["precursor_mz"],
                    "library-name": spec["library-name"],
                    "library-precursor_type": spec["library-precursor_type"],
                    "library-idx": len(all_library_spectra_abstract)
                }
                all_library_spectra_abstract.append(spec_abstract)
            entropy_search.abstract_library_spectra = all_library_spectra_abstract

            spectral_library[charge] = entropy_search

        self.status["message"] = f"Saving index for {library_name}..."
        # Save index
        with open(file_library_index, "wb") as f:
            pickle.dump(spectral_library, f)
        self.spectral_library = spectral_library
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
            return convert_float(x)
        except:
            try:
                return float(x.split()[0])
            except:
                return -1
    spec = standardize_spectrum(spec, standardize_info={
        "id": [["db#"], "", str],
        "scan": [["_scan_number"], -1, int],
        "name": [["title"], "", str],
        "rt": [["retentiontime"], -1, convert_float],
        "precursor_mz": [["precursormz", "pepmass"], -1, convert_precursor_mz],
        "ion_mode": [["ionmode"], "", str],
        "precursor_type": [["precursortype"], "", str],
        "charge": [[], "", str],
        "name": [["title"], "", str],
    })

    charge = 0
    if spec["charge"]:
        if spec["charge"][-1] in {"+", "-"}:
            c = spec["charge"][-1]
            try:
                charge = int(spec["charge"][:-1])
                if c == "-":
                    charge = -charge
            except:
                charge = 0
        else:
            try:
                charge = int(spec["charge"])
            except:
                charge = 0

    # Infer precursor charge from ion mode
    if (charge == 0) and (ion_mode := spec["ion_mode"]):
        charge = {"n": -1, "p": 1}.get(ion_mode[0].lower(), "")

    # Guess precursor charge from adduct
    if (charge == 0) and (len(spec["precursor_type"]) > 0):
        charge = {"+": 1, "-": -1}.get(spec["precursor_type"][-1], "")

    spec["charge"] = charge
    return spec


if __name__ == '__main__':
    para = {
        "ms1_tolerance_in_da": 0.01,
        "ms2_tolerance_in_da": 0.02,
        "top_n": 10,
        "cores": 1,

        "file_query": r"/p/github/EntropySearch/test/a.msp",
        "file_library": r"/p/github/EntropySearch/test/a.msp",
        # "file_query": r"/p/FastEntropySearch/gui/test/input/test.mgf",
        # "file_library": r"/p/FastEntropySearch/gui/test/input/test.mgf",
        "file_output": r"/p/github/EntropySearch/test/result.csv",
    }
    entropy_search = EntropySearch(para["ms2_tolerance_in_da"])
    entropy_search.load_spectral_library(Path(para["file_library"]))
    all_results = entropy_search.search_file(
        Path(para["file_query"]), para["top_n"], para["ms1_tolerance_in_da"], para["ms2_tolerance_in_da"], cores=para["cores"])
    a = 1
    # test = entropy_search.get_one_spectrum_result(5, para["top_n"], para["ms1_tolerance_in_da"], para["ms2_tolerance_in_da"])
    # print(test)
    # test2 = entropy_search.get_one_library_spectrum(charge=1, library_idx=1489)
    # print(test2)
