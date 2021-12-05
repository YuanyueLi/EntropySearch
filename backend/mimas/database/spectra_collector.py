import numpy as np
import pickle
from pathlib import PurePath
from typing import Union

from mimas.file_io import spec_file
import hashlib


def _md5(fname: str):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


class SpectraCollector:
    def __init__(self):
        self.library = {}
        self.information = []

    def add_index_for_hybrid_search(self, ms2_da, min_intensity=0.05, max_peak_number=10):
        for charge in self.library:
            all_spec, precursor_index = self.library[charge][0:2]
            all_mz_idx = []
            all_neutral_loss_idx = []
            for i, (precursor_mz, spec, _) in enumerate(all_spec):
                if len(spec) == 0:
                    continue

                spec_idx = spec[spec[:, 1] > min_intensity]
                if len(spec_idx) > max_peak_number:
                    spec_idx = spec_idx[np.argsort(-spec_idx[:, 1])][:max_peak_number]

                # Add index for m/z
                mz_idx = spec_idx[:, 0] // ms2_da
                for idx in mz_idx:
                    idx = int(idx)
                    if idx >= len(all_mz_idx):
                        all_mz_idx += [set() for _ in range(idx - len(all_mz_idx) + 1)]
                    all_mz_idx[idx].add(i)

                # Add index for neutral loss
                nl_idx = (precursor_mz - spec_idx[:, 0]) // ms2_da
                for idx in nl_idx:
                    idx = int(idx)
                    if idx >= len(all_neutral_loss_idx):
                        all_neutral_loss_idx += [set() for _ in range(idx - len(all_neutral_loss_idx) + 1)]
                    all_neutral_loss_idx[idx].add(i)

            self.library[charge].append([all_mz_idx, all_neutral_loss_idx])

    @staticmethod
    def standardize_query_spectrum(spec_info):
        spec_file.standardize_spectrum(spec_info, {
            "precursor_mz": [["precursormz"], None, float],
            "adduct": [["precursortype", "precursor_type"], "", str],
            "name": [["title"], None, None],
            "id": [["spectrum_id", "db#", "spectrumid", "NISTNO"], None, None],
            "scan_number": [["_scan_number"], None, int],
            "rt": [["retention_time", "retentiontime"], None, float]
        })
        if spec_info["adduct"] == "" and \
                "precursor_charge" in spec_info and spec_info["precursor_charge"] is not None:
            if float(spec_info["precursor_charge"]) > 0:
                spec_info["adduct"] = "[M+H]+"
            elif float(spec_info["precursor_charge"]) < 0:
                spec_info["adduct"] = "[M-H]-"

    def preprocess_peaks(self, func_process, threads, *args):
        for charge in self.library:
            all_spec = self.library[charge][0]
            for i in range(len(all_spec)):
                all_spec[i][1] = func_process(all_spec[i][0], all_spec[i][1], *args)

    def read_spectra_file(self, file_spectra_list, force_rebuild_index=False):
        for file_spectra, file_index in file_spectra_list:
            self._read_one_spectra_file(file_spectra, file_index, force_rebuild_index=force_rebuild_index)

        # Index spectral information
        library_new = {}
        for charge in self.library:
            collection = self.library[charge]
            collection = [collection[i] for i in np.argsort([x[0] for x in collection])]
            precursor_mz_array = np.array([x[0] for x in collection])
            library_new[charge] = [collection, precursor_mz_array]
        self.library = library_new

    def _read_one_spectra_file(self, file_spectra, file_index, force_rebuild_index=False):
        if force_rebuild_index:
            data = self._index_one_spectra_file(file_spectra, file_index)
        else:
            try:
                data = file_index.load_data()
            except Exception as e:
                data = self._index_one_spectra_file(file_spectra, file_index)

        # Merge all spectra file together.
        data_library, data_information = data

        cur_spec_num = len(self.information)
        for i in data_information:
            i["library_filename"] = file_spectra.get_filename()
        self.information += data_information

        for charge in data_library:
            for spec in data_library[charge]:
                spec[-1] += cur_spec_num
            if charge not in self.library:
                self.library[charge] = []
            self.library[charge] += data_library[charge]
        return data

    def _index_one_spectra_file(self, file_spectra, file_index):
        collections_spec = {"+": [], "-": []}
        collections_information = []

        for spec_info in file_spectra.read_one_spectrum(ms2_only=True):
            try:
                spec_file.standardize_spectrum(spec_info, {
                    "precursor_mz": [["precursormz"], None, float],
                    "adduct": [["precursortype", "precursor_type"], "", str],
                    "name": [[], None, None],
                    "id": [["spectrum_id", "db#", "spectrumid"], None, None],
                    "inchikey": [[], None, None]
                })
            except Exception as e:
                print("Error in parse: ", spec_info)
                continue

            # Organize spectra data
            self._add_spec(spec_info, collections_spec, collections_information)

        # Organize collections
        collections_final = {}
        for charge in collections_spec:
            collection = collections_spec[charge]
            collection = [collection[i] for i in np.argsort([x[0] for x in collection])]
            collections_final[charge] = collection

        # Write result file
        index_data = [collections_final, collections_information]
        file_index.save_data(index_data)
        return index_data

    @staticmethod
    def _add_spec(spec_info: dict, collections_spec: dict, collections_information):
        peaks = [x for x in spec_info["peaks"] if x[0] > 0 and x[1] > 0]
        precursor_mz = spec_info["precursor_mz"]

        if len(peaks) > 0 and \
                len(spec_info["adduct"]) > 0 and \
                spec_info["adduct"][-1] in {"+", "-"} and \
                (precursor_mz is not None) and \
                precursor_mz > 0:
            charge = spec_info["adduct"][-1]
            collections_spec = collections_spec[charge]

            db_spec = {"library_name": spec_info["name"],
                       "library_inchikey": spec_info["inchikey"],
                       "library_id": spec_info["id"],
                       "library_adduct": spec_info["adduct"],
                       "library_precursor_mz": spec_info["precursor_mz"]}

            collections_spec.append(
                [float(precursor_mz), np.array(peaks, dtype=np.float32), len(collections_information)])
            collections_information.append(db_spec)

    def get_information(self, library_id):
        return self.information[library_id]

    def get_candidate_spectra(
            self,
            precursor_mz: float,
            adduct: str,
            delta_ppm: float = None,
            delta_da: float = None) -> [{}]:
        if len(adduct) == 0:
            return []
        charge = adduct[-1]
        all_spec, precursor_mz_array = self.library[charge][0:2]

        if delta_ppm:
            delta_da = precursor_mz * delta_ppm * 1e-6

        mz_min = precursor_mz - delta_da
        mz_max = precursor_mz + delta_da

        idx_left = np.searchsorted(precursor_mz_array, mz_min, side="left")
        idx_right = np.searchsorted(precursor_mz_array, mz_max, side="right")

        return all_spec[idx_left: idx_right]

    def get_candidate_spectra_for_hybrid_search(
            self,
            precursor_mz: float,
            precursor_type: str,
            peaks: np.ndarray,
            ms2_da: float,
            min_intensity=0.05, max_peak_number=10) -> [{}]:
        if len(precursor_type) == 0 or len(peaks) == 0:
            return []
        charge = precursor_type[-1]
        all_spec, _, (library_mz_idx, library_nl_idx) = self.library[charge][0:3]
        result = set()

        peaks_idx = peaks[peaks[:, 1] > min_intensity]
        if len(peaks_idx) > max_peak_number:
            peaks_idx = peaks_idx[np.argsort(-peaks_idx[:, 1])][:max_peak_number]
        for mz in peaks_idx[:, 0]:
            mz_idx = int(mz // ms2_da)
            try:
                result |= library_mz_idx[mz_idx - 1]
                result |= library_mz_idx[mz_idx]
                result |= library_mz_idx[mz_idx + 1]
            except Exception as e:
                pass

        peaks_idx = precursor_mz - peaks_idx[:, 0]
        for nl in peaks_idx:
            nl_idx = int(nl // ms2_da)
            try:
                result |= library_nl_idx[nl_idx - 1]
                result |= library_nl_idx[nl_idx]
                result |= library_nl_idx[nl_idx + 1]
            except Exception as e:
                pass

        return [all_spec[x] for x in result]


if __name__ == '__main__':
    # Test
    filename_spec = r"D:\test\db\test.msp"

    db = SpectraCollector()
    db.read_spectra_file(file_spectra=filename_spec)
    spec = db.get_candidate_spectra(precursor_mz=202.04, adduct="[M+H]+", delta_da=0.05)
    print(spec)
