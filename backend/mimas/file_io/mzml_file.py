import numpy as np


def read_all_spectra(filename_input):
    from mimas.ms.run import Run
    import pymzml
    run = Run()
    mzml_data = pymzml.run.Reader(filename_input)
    for n, spec_raw in enumerate(mzml_data):
        spec = np.asarray(spec_raw.peaks('raw'), dtype=np.float32, order="C")
        spec_info = {
            "ms_level": spec_raw.ms_level,
            '_scan_number': spec_raw.id_dict["scan"],
            'peaks': spec,
            'rt': spec_raw.scan_time_in_minutes() * 60,
            'precursor_mz': spec_raw.selected_precursors[0].get('mz', None) \
                if len(spec_raw.selected_precursors) > 0 else None,
            'precursor_charge': spec_raw.selected_precursors[0].get('charge', None) \
                if len(spec_raw.selected_precursors) > 0 else None,
        }
        run.add_scan(spec_info)

    run.finish_adding_data()
    return run


def read_one_spectrum(filename_input):
    import pymzml
    """
    Read information from .mzml file.
    :param filename_input: a .mzML file.
    :return: a dict contains a list with key 'spectra'.
        The list contains multiple dict, one dict represent a single spectrum's informaiton.
    """
    run = pymzml.run.Reader(filename_input)
    for n, spec_raw in enumerate(run):
        spec = np.asarray(spec_raw.peaks('raw'), dtype=np.float32, order="C")
        spec_info = {
            "ms_level": spec_raw.ms_level,
            '_scan_number': spec_raw.id_dict["scan"],
            'peaks': spec,
            'rt': spec_raw.scan_time_in_minutes() * 60,
            'precursor_mz': spec_raw.selected_precursors[0].get('mz', None) \
                if len(spec_raw.selected_precursors) > 0 else None,
            'precursor_charge': spec_raw.selected_precursors[0].get('charge', None) \
                if len(spec_raw.selected_precursors) > 0 else None,
        }
        yield spec_info
