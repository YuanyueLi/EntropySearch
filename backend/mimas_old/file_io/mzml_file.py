import numpy as np



def read_one_spectrum(filename_input):
    import pymzml
    """
    Read information from .mzml file.
    :param filename_input: a .mzML file.
    :return: a dict contains a list with key 'spectra'.
        The list contains multiple dict, one dict represent a single spectrum's informaiton.
    """
    run = pymzml.run.Reader(filename_input, obo_version="4.1.33")
    for n, spec_raw in enumerate(run):
        spec = np.asarray(spec_raw.peaks('raw'), dtype=np.float32, order="C")
        spec_info = {
            "ms_level": spec_raw.ms_level,
            '_scan_number': n + 1,
            'peaks': spec,
            'rt': spec_raw.scan_time_in_minutes() * 60,
            'precursor_mz': spec_raw.selected_precursors[0].get('mz', None) \
                if len(spec_raw.selected_precursors) > 0 else None,
            'precursor_charge': spec_raw.selected_precursors[0].get('charge', None) \
                if len(spec_raw.selected_precursors) > 0 else None,
        }
        if spec_info["precursor_charge"] is None:
            if spec_raw["negative scan"]:
                spec_info["precursor_charge"] = -1
            elif spec_raw["positive scan"]:
                spec_info["precursor_charge"] = 1
        yield spec_info
