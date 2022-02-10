import logging

import numpy as np


def _parse_info(info):
    result = {}

    item = info.strip().split('=')
    if len(item) < 2:
        return result

    info = item[0].strip()
    value = item[1].strip() if len(item) == 2 else '='.join(item[1:]).strip()

    if info == 'PEPMASS':
        try:
            result = dict(precursor_mz=float(value))
        except ValueError:
            result = dict(precursor_mz=float(value.split()[0]))

    elif info == 'CHARGE':
        _charge_dict = {'-': -1, '+': 1}
        if value[-1] in _charge_dict:
            charge = _charge_dict[value[-1]] * int(value[:-1])
        elif value[0] in _charge_dict:
            charge = _charge_dict[value[0]] * int(value[1:])
        else:
            charge = int(value)
        result = dict(charge=charge)
    else:
        result = {info.lower(): value}

    return result


def read(stream_input):
    """
    Read information from .mgf file.
    :param stream_input: a stream for input.
    :return: a dict contains a list with key 'spectra'.
        The list contains multiple dict, one dict represent a single spectrum's informaiton.
    """

    exp = {
        'spectra': []
    }

    for spectrum_info in read_one_spectrum(stream_input):
        exp['spectra'].append(spectrum_info)
    return exp


def read_one_spectrum(filename_input: str, include_raw=0, **kwargs) -> dict:
    fi = open(filename_input, "rt")
    raw = []
    scan_number = 1
    spectrum_info = {
        '_scan_number': scan_number,
        "ms_level": 2,
        'peaks': []
    }
    is_spectrum_start = 0

    for line in fi:
        if not isinstance(line, str):
            line = line.decode()

        if include_raw:
            raw.append(line)

        line = line.strip()

        if len(line) > 0 and line[0] != '#':
            if line.find('BEGIN IONS') >= 0:
                is_spectrum_start = 1

            elif line.find('END IONS') >= 0:
                if include_raw:
                    spectrum_info['raw'] = "".join(raw)

                yield spectrum_info
                raw = []
                is_spectrum_start = 0
                scan_number += 1
                spectrum_info = {
                    "ms_level": 2,
                    '_scan_number': scan_number,
                    'peaks': []
                }

            elif is_spectrum_start:
                if line.find('=') >= 0:
                    spectrum_info.update(_parse_info(line))
                else:
                    items = line.split()
                    assert len(items) >= 2, "Error found when parse {}".format(line)
                    spectrum_info['peaks'].append((float(items[0]), float(items[1])))
    fi.close()


def write(exp, filename_output: str):
    with open(filename_output, 'wt') as fo:
        for spec in exp:
            write_spectrum(spec, fo)
    pass


_write_special = {'precursor_mz', 'raw_scan_num', 'ms_level', 'retention_time', 'precursor_charge', 'spectrum'}


def write_spectrum(spec, fileout):
    out_str = ['BEGIN IONS']

    def __add_to_output_str_if_exist(str_pre, str_suffix, item_name):
        if item_name in spec:
            out_str.append(str_pre + str(spec[item_name]) + str_suffix)

    __add_to_output_str_if_exist('PEPMASS=', '', 'precursor_mz')
    __add_to_output_str_if_exist('SCANS=', '', 'raw_scan_num')
    __add_to_output_str_if_exist('MSLEVEL=', '', 'ms_level')
    __add_to_output_str_if_exist('RTINSECONDS=', '', 'retention_time')

    if 'precursor_charge' in spec:
        out_str.append('CHARGE=' + str(abs(spec['precursor_charge'])) +
                       ('+' if spec['precursor_charge'] >= 0 else '-'))

    for item in spec:
        if item not in _write_special:
            out_str.append(item.upper() + "=" + str(spec[item]))

    for peak in spec['spectrum']:
        out_str.append(str(peak[0]) + '\t' + str(peak[1]))

    out_str.append('END IONS\n')
    fileout.write('\n'.join(out_str))


def write_spec(spec_info: dict, spec_data: np.ndarray, filename_output: str):
    """
    Write spectrum to a mgf file.
    :param spec_info:
    :param spec_data:
    :param filename_output:
    :return: None
    """
    if filename_output[-3:] != "mgf":
        logging.warning("Output filename is not a mgf file!")

    with open(filename_output, 'wt') as fo:
        _write_spec(spec_info, spec_data, fo)


def _write_spec(spec_info, spec_data, fileout):
    out_str = ['BEGIN IONS']

    def __add_to_output_str_if_exist(str_pre, str_suffix, item_name):
        if item_name in spec_info:
            out_str.append(str_pre + str(spec_info[item_name]) + str_suffix)

    __add_to_output_str_if_exist('PEPMASS=', '', 'precursor_mz')
    __add_to_output_str_if_exist('SCANS=', '', 'raw_scan_num')
    __add_to_output_str_if_exist('MSLEVEL=', '', 'ms_level')
    __add_to_output_str_if_exist('RTINSECONDS=', '', 'retention_time')

    if 'precursor_charge' in spec_info:
        out_str.append('CHARGE=' + str(abs(spec_info['precursor_charge'])) +
                       ('+' if spec_info['precursor_charge'] >= 0 else '-'))

    for peak in spec_data:
        out_str.append(str(peak[0]) + '\t' + str(peak[1]))

    out_str.append('END IONS\n')
    fileout.write('\n'.join(out_str))
