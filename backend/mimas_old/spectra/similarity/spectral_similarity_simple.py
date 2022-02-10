import numpy as np
import scipy.stats
from typing import Union

from .tools import clean_spectrum, match_peaks_in_spectra, normalize_distance


def _weight_intensity_for_entropy(x):
    if sum(x) > 0:
        entropy_x = scipy.stats.entropy(x)
        if entropy_x >= 3:
            return x
        else:
            WEIGHT_START = 0.25
            WEIGHT_SLOPE = 0.25

            weight = WEIGHT_START + WEIGHT_SLOPE * entropy_x
            x = np.power(x, weight)
            x = x / sum(x)
            return x


def entropy_distance(p, q):
    p = _weight_intensity_for_entropy(p)
    q = _weight_intensity_for_entropy(q)

    merged = p + q
    entropy_increase = 2 * scipy.stats.entropy(merged) - scipy.stats.entropy(p) - scipy.stats.entropy(q)
    return entropy_increase


def entropy_similarity(spectrum_query: Union[list, np.ndarray], spectrum_library: Union[list, np.ndarray],
                       ms2_ppm: float = None, ms2_da: float = None,
                       need_clean_spectra: bool = True) -> float:
    """
    Calculate the distance between two spectra, find common peaks.
    If both ms2_ppm and ms2_da is defined, ms2_da will be used.
    :param spectrum_query:
    :param spectrum_library:
    :param ms2_ppm:
    :param ms2_da:
    :param need_clean_spectra: Normalize spectra before comparing, required for not normalized spectrum.
    :return: Entropy similarity between two spectra
    """
    spectrum_query = np.asarray(spectrum_query, dtype=np.float32)
    spectrum_library = np.asarray(spectrum_library, dtype=np.float32)
    if need_clean_spectra:
        spectrum_query = clean_spectrum(spectrum_query, ms2_ppm=ms2_ppm, ms2_da=ms2_da)
        spectrum_library = clean_spectrum(spectrum_library, ms2_ppm=ms2_ppm, ms2_da=ms2_da)

    # Calculate similarity
    if spectrum_query.shape[0] > 0 and spectrum_library.shape[0] > 0:
        spec_matched = match_peaks_in_spectra(spec_a=spectrum_query, spec_b=spectrum_library,
                                              ms2_ppm=ms2_ppm, ms2_da=ms2_da)
        dist = entropy_distance(spec_matched[:, 1], spec_matched[:, 2])
        return 1 - dist / np.log(4)
    else:
        return 0
