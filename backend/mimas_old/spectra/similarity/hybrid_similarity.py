import numpy as np
from typing import Union
import scipy.stats

from .tools import clean_spectrum, match_peaks_in_spectra_output_number
from .spectral_similarity_simple import entropy_distance


def merge_matched_id_array(peaks_match_array_1, peaks_match_array_2, peaks_2):
    for i in range(len(peaks_match_array_1)):
        if peaks_match_array_2[i, 1] >= 0:
            if peaks_match_array_1[i, 1] < 0 or \
                    peaks_2[peaks_match_array_2[i, 1], 1] > peaks_2[peaks_match_array_1[i, 1], 1]:
                peaks_match_array_1[i, 1] = peaks_match_array_2[i, 1]
    return peaks_match_array_1


def calculate_entropy_similarity(peaks_match_array, peaks_a, peaks_b):
    p_a = np.copy(peaks_a[:, 1])
    p_b = np.copy(peaks_b[:, 1])
    p_ba = np.zeros_like(p_b)
    for a, b in peaks_match_array:
        if b >= 0:
            p_ba[b] += p_a[a]
            p_a[a] = 0

    spectral_distance = entropy_distance(np.concatenate([p_a, p_ba]),
                                         np.concatenate([np.zeros_like(p_a), p_b]))
    spectral_similarity = 1 - spectral_distance / np.log(4)
    return spectral_similarity

    e_a = scipy.stats.entropy(np.concatenate([p_a, p_ba]))
    e_b = scipy.stats.entropy(p_b)
    p_b += p_ba
    e_ab = scipy.stats.entropy(np.concatenate([p_a, p_b]))
    distance = 2 * e_ab - e_a - e_b
    return 1 - distance / np.log(4)


def calculate_spectral_entropy(peaks):
    return scipy.stats.entropy(peaks[:, 1])


def similarity(peaks_query: Union[list, np.ndarray], peaks_library: Union[list, np.ndarray],
               precursor_mz_delta: float, method: str = "bonanza",
               ms2_ppm: float = None, ms2_da: float = None,
               need_clean_spectra: bool = True) -> float:
    """
    Calculate the similarity between two spectra, find common peaks.
    If both ms2_ppm and ms2_da is defined, ms2_da will be used.
    :param peaks_query:
    :param peaks_library:
    :param precursor_mz_delta: query precursor mz - library precursor mz
    :param method: Supported methods: "bonanza"
    :param ms2_ppm:
    :param ms2_da:
    :param need_clean_spectra: Normalize spectra before comparing, required for not normalized spectrum.
    :return: Similarity between two spectra
    """
    peaks_query = np.asarray(peaks_query, dtype=np.float32)
    peaks_library = np.asarray(peaks_library, dtype=np.float32)
    if need_clean_spectra:
        peaks_query = clean_spectrum(peaks_query, ms2_ppm=ms2_ppm, ms2_da=ms2_da)
        peaks_library = clean_spectrum(peaks_library, ms2_ppm=ms2_ppm, ms2_da=ms2_da)

    # Calculate similarity
    if peaks_query.shape[0] > 0 and peaks_library.shape[0] > 0:
        peaks_matched_ori = match_peaks_in_spectra_output_number(spec_a=peaks_query,
                                                                 spec_b=peaks_library,
                                                                 ms2_ppm=ms2_ppm, ms2_da=ms2_da)
        peaks_query[:, 0] -= precursor_mz_delta
        peaks_matched_shift = match_peaks_in_spectra_output_number(spec_a=peaks_query,
                                                                   spec_b=peaks_library,
                                                                   ms2_ppm=ms2_ppm, ms2_da=ms2_da)
        peaks_query[:, 0] += precursor_mz_delta

        peaks_matched_id_array = merge_matched_id_array(peaks_matched_ori, peaks_matched_shift, peaks_library)

        if np.sum(peaks_matched_id_array[:, 1] >= 0) == 0:
            spectral_similarity = 0
        else:
            spectral_similarity = calculate_entropy_similarity(peaks_matched_id_array, peaks_query, peaks_library)
        return spectral_similarity
    return 0.


def similarity_old(spectrum_query: Union[list, np.ndarray], spectrum_library: Union[list, np.ndarray],
                   precursor_mz_delta: float, method: str = "bonanza",
                   ms2_ppm: float = None, ms2_da: float = None,
                   need_clean_spectra: bool = True) -> float:
    """
    Calculate the similarity between two spectra, find common peaks.
    If both ms2_ppm and ms2_da is defined, ms2_da will be used.
    :param spectrum_query:
    :param spectrum_library:
    :param precursor_mz_delta: library precursor mz - query precursor mz
    :param method: Supported methods: "bonanza"
    :param ms2_ppm:
    :param ms2_da:
    :param need_clean_spectra: Normalize spectra before comparing, required for not normalized spectrum.
    :return: Similarity between two spectra
    """
    # TODO: Might have bugs here!
    spectrum_query = np.asarray(spectrum_query, dtype=np.float32)
    spectrum_library = np.asarray(spectrum_library, dtype=np.float32)
    if need_clean_spectra:
        spectrum_query = clean_spectrum(spectrum_query, ms2_ppm=ms2_ppm, ms2_da=ms2_da)
        spectrum_library = clean_spectrum(spectrum_library, ms2_ppm=ms2_ppm, ms2_da=ms2_da)

    # Calculate similarity
    if spectrum_query.shape[0] > 0 and spectrum_library.shape[0] > 0:

        spec_matched_ori = match_peaks_in_spectra_output_number(spec_a=spectrum_query,
                                                                spec_b=spectrum_library,
                                                                ms2_ppm=ms2_ppm, ms2_da=ms2_da)
        spectrum_query[:, 0] += precursor_mz_delta
        spec_matched_shift = match_peaks_in_spectra_output_number(spec_a=spectrum_query,
                                                                  spec_b=spectrum_library,
                                                                  ms2_ppm=ms2_ppm, ms2_da=ms2_da)
        spectrum_query[:, 0] -= precursor_mz_delta

        match_info_ori = np.where(np.bitwise_and(spec_matched_ori[:, 0] > 0, spec_matched_ori[:, 1] > 0))[0]
        match_info_shift = np.where(np.bitwise_and(spec_matched_shift[:, 0] > 0, spec_matched_shift[:, 1] > 0))[0]

        # Add all score to result
        result = []
        for i in match_info_ori:
            query_i, library_i = spec_matched_ori[i]
            score_i = spectrum_query[query_i, 1] * spectrum_library[library_i, 1]
            result.append((score_i, query_i, library_i))
        for i in match_info_shift:
            query_i, library_i = spec_matched_shift[i]
            score_i = spectrum_query[query_i, 1] * spectrum_library[library_i, 1]
            result.append((score_i, query_i, library_i))
        result.sort(key=lambda x: -x[0])

        if len(result) == 0:
            return 0

        # Calculate score matched.
        query_set = set()
        library_set = set()
        score_matched = 0.
        for item in result:
            if item[1] not in query_set and item[2] not in library_set:
                query_set.add(item[1])
                library_set.add(item[2])
                score_matched += item[0]

        # Calculate score unmatched.
        score_unmatched = 0.
        for i in range(spectrum_query.shape[0]):
            if i not in query_set:
                score_unmatched += spectrum_query[i, 1] ** 2
        for i in range(spectrum_library.shape[0]):
            if i not in library_set:
                score_unmatched += spectrum_library[i, 1] ** 2

        return 1 / (1 + score_unmatched / score_matched)
    return 0.
