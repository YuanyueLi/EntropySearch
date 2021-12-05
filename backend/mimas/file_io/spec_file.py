import zipfile
import gzip

import numpy as np

from . import mgf_file
from . import msp_file
from . import mzml_file
from . import hdf5_file
from . import raw_file
import pickle


def read_all_spectra(filename_input: str, file_type: object = None, **kwargs: object):
    if file_type is None:
        file_type = guess_file_type_from_file_name(filename_input)

    if file_type == ".mzml":
        return mzml_file.read_all_spectra(filename_input=filename_input, **kwargs)
    else:
        raise NotImplementedError()


def read_one_spectrum(filename_input: str, file_type: object = None, ms2_only=False, **kwargs: object) -> dict:
    """

    :param filename_input:
    :param file_type:
    :param ms2_only: Only output MS/MS spectra
    :param kwargs:
    :return: a dictionary contains the following items:
        ms_level: 1, 2, 3, ...
        peaks: list or numpy array, For mzML file, it is a numpy array.
        precursor_mz: float or None
        _scan_number: start from 1, int
        rt: retention time, float or None. For mzML file, it is in second. For msp/mgf formats, it is the same as in the original file.
    """
    if file_type is None:
        file_type = guess_file_type_from_file_name(filename_input)

    if file_type == ".msp":
        spectral_generator = msp_file.read_one_spectrum(filename_input=filename_input, **kwargs)
    elif file_type == ".mgf":
        spectral_generator = mgf_file.read_one_spectrum(filename_input=filename_input, **kwargs)
    elif file_type == ".mzml":
        spectral_generator = mzml_file.read_one_spectrum(filename_input=filename_input)
    elif file_type == ".hdf5":
        spectral_generator = hdf5_file.read_one_spectrum(filename_input=filename_input)
    elif file_type == ".raw":
        spectral_generator = raw_file.read_one_spectrum(filename_input=filename_input)
    else:
        raise NotImplementedError()
    for i, spec in enumerate(spectral_generator):
        spec_template = {
            '_scan_number': i,
            "ms_level": 2
        }
        i += 1

        spec_template.update(spec)
        spec = spec_template

        if ms2_only and spec["ms_level"] != 2:
            continue

        if len(spec["peaks"]) == 0:
            spec["peaks"] = np.empty((0, 2), dtype=np.float32)
        else:
            spec["peaks"] = np.asarray(spec["peaks"], dtype=np.float32)

        yield spec


def guess_file_type_from_file_name(filename_input):
    file_type = None
    if filename_input[-4:].lower() == ".zip":
        fzip_all = zipfile.ZipFile(filename_input)
        fzip_list = zipfile.ZipFile.namelist(fzip_all)
        # Only select the first file for the zip file
        if fzip_list[0][-4:].lower() == ".msp":
            file_type = ".msp"
        elif fzip_list[0][-4:].lower() == ".mgf":
            file_type = ".mgf"
    elif filename_input[-3:].lower() == ".gz":
        if filename_input[-8:-3].lower() == ".mzml":
            file_type = ".mzml"
    else:
        if filename_input[-4:].lower() == ".msp":
            file_type = ".msp"
        elif filename_input[-4:].lower() == ".mgf":
            file_type = ".mgf"
        elif filename_input[-5:].lower() == ".mzml":
            file_type = ".mzml"
        elif filename_input[-5:].lower() == ".hdf5":
            file_type = ".hdf5"
        elif filename_input[-4:].lower() == ".raw":
            file_type = ".raw"
        elif filename_input.split(".")[-2].lower() == "msp":
            file_type = ".msp"
        elif filename_input.split(".")[-2].lower() == "mgf":
            file_type = ".mgf"
        elif filename_input.split(".")[-2].lower() == "mzml":
            file_type = ".mzml"
    return file_type


def write_one_spectrum(fo, spec, output_type: str):
    if output_type == ".msp":
        msp_file.write_one_spectrum(fo, spec)
    else:
        raise NotImplementedError()


def standardize_spectrum(spec_info: dict, standardize_info: dict):
    """
    :param spec_info: spectrum info to standardize
    :param standardize_info: {wanted_key:[[candidate_keys],default_value,default_type_function]}
    :return: None
    """
    for key_target, (key_all_candidates, value_default, value_type) in standardize_info.items():
        key_all_candidates_new = [key_target] + key_all_candidates
        for key_candidate in key_all_candidates_new:
            if key_candidate in spec_info:
                if key_target != key_candidate:
                    if value_type is None:
                        spec_info[key_target] = spec_info.pop(key_candidate)
                    else:
                        try:
                            spec_info[key_target] = value_type(spec_info.pop(key_candidate))
                        except:
                            spec_info[key_target] = value_default
                else:
                    if value_type is not None:
                        try:
                            spec_info[key_target] = value_type(spec_info[key_target])
                        except:
                            spec_info[key_target] = value_default
                break
        else:
            spec_info[key_target] = value_default

        for key_candidate in key_all_candidates:
            if key_candidate in spec_info:
                spec_info.pop(key_candidate)


def check_spectral_items(spec_info: dict, check_keys: list):
    """
    Check if the keys in check_keys are in spec_info
    :param spec_info: spectrum info to check
    :param check_keys: keys to check
    """
    for k in check_keys:
        if k not in spec_info:
            return False
        if spec_info[k] is None:
            return False
    return True


class SpecFile:
    def __init__(self, filename, file_type=None):
        self.filename = filename
        if file_type is None:
            self.file_type = guess_file_type_from_file_name(filename)
        else:
            self.file_type = file_type

    def get_filename(self):
        return self.filename

    def read_one_spectrum(self, ms2_only=True, **kwargs: object):
        if self.file_type == ".msp":
            spectral_generator = msp_file.read_one_spectrum(filename_input=self.filename, **kwargs)
        elif self.file_type == ".mgf":
            spectral_generator = mgf_file.read_one_spectrum(filename_input=self.filename, **kwargs)
        elif self.file_type == ".mzml":
            spectral_generator = mzml_file.read_one_spectrum(filename_input=self.filename)
        elif self.file_type == ".hdf5":
            spectral_generator = hdf5_file.read_one_spectrum(filename_input=self.filename)
        elif self.file_type == ".raw":
            spectral_generator = raw_file.read_one_spectrum(filename_input=self.filename)
        else:
            raise NotImplementedError()
        for i, spec in enumerate(spectral_generator):
            spec_template = {
                '_scan_number': i,
                "ms_level": 2,
                'rt': -1,
                'precursor_mz': -1,
                'precursor_charge': -1,
                "peaks": []
            }
            i += 1

            spec_template.update(spec)
            spec = spec_template

            if ms2_only and spec["ms_level"] != 2:
                continue

            if len(spec["peaks"]) == 0:
                spec["peaks"] = np.empty((0, 2), dtype=np.float32)
            else:
                spec["peaks"] = np.asarray(spec["peaks"], dtype=np.float32)

            yield spec


class IndexFile:
    def __init__(self, spec_filename, para: str):
        import hashlib
        self.filename = spec_filename + "-" + hashlib.md5(pickle.dumps(para)).hexdigest() + ".idx"

    def save_data(self, data):
        pickle.dump(data, open(self.filename, "wb"))

    def read_data(self):
        return pickle.load(open(self.filename, "rb"))
