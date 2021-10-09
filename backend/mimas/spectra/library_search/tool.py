import numpy as np
from mimas.spectra.similarity.tools import clean_spectrum


def preprocess_peaks(precursor_mz, peaks, noise, precursor_removal=None, ms2_da=None, ms2_ppm=None):
    if precursor_removal is not None:
        peaks = clean_spectrum(peaks, max_mz=precursor_mz - precursor_removal, ms2_da=ms2_da, ms2_ppm=ms2_ppm)
    else:
        peaks = clean_spectrum(peaks, max_mz=None, ms2_da=ms2_da, ms2_ppm=ms2_ppm)

    if peaks.shape[0] > 0:
        spec_max = np.max(peaks[:, 1])
        peaks = peaks[peaks[:, 1] > spec_max * noise]
        spec_sum = np.sum(peaks[:, 1])
        peaks[:, 1] /= spec_sum
    return peaks
