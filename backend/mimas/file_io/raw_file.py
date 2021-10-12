import numpy as np


def read_one_spectrum(filename_input: str):
    """Load raw thermo data as a dictionary.

    Args:
        filename_input (str): The name of a Thermo .raw file.

    Returns:
         a dict contains a list with key 'spectra'.
        The list contains multiple dict, one dict represent a single spectrum's informaiton.

    """
    import logging
    from alphapept.pyrawfilereader import RawFileReader
    rawfile = RawFileReader(filename_input)

    spec_indices = np.array(
        range(rawfile.FirstSpectrumNumber, rawfile.LastSpectrumNumber + 1)
    )

    for scan_number in spec_indices:
        try:
            ms_order = rawfile.GetMSOrderForScanNum(scan_number)
            rt = rawfile.RTFromScanNum(scan_number)

            if ms_order == 2:
                mono_mz, charge = rawfile.GetMS2MonoMzAndChargeFromScanNum(scan_number)
            else:
                mono_mz, charge = 0, 0

            masses, intensity = rawfile.GetCentroidMassListFromScanNum(scan_number)
            spec = {
                "ms_level": ms_order,
                '_scan_number': scan_number,
                'rt': rt,
                'precursor_mz': mono_mz,
                'precursor_charge': charge,
                "peaks": np.ascontiguousarray(np.array([masses, intensity]).T)
            }
            yield spec

        except Exception as e:
            logging.info(f"Bad scan={scan_number} in raw file '{filename_input}'")

    rawfile.Close()