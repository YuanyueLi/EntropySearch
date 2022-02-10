import numpy as np
import pandas as pd
import datetime

from mimas.database.spectra_collector import SpectraCollector
from mimas.file_io import spec_file
from mimas.helper import multiplecore
from mimas.spectra.similarity import spectral_similarity_simple
from mimas.spectra.similarity import hybrid_similarity
from . import tool


def _read_spectral_library(para):
    para_search = para["search"]
    spec_library = SpectraCollector()
    spec_library.read_spectra_file(para["file_library"])
    if para_search["clean_spectra"]:
        spec_library.preprocess_peaks(tool.preprocess_peaks, para["threads"],
                                      para_search["noise"], para_search["precursor_removal"],
                                      para_search.get("ms2_da", None), para_search.get("ms2_ppm", None))
    return spec_library


def _merge_result(_, cur_result, similarity_result):
    if cur_result:
        # Add spectral information
        similarity_result.add_result_list(cur_result)


def untarget_search(search_type, parameter):
    """
    :param search_type: "identity" or "hybrid"
    :param parameter: the following fields are required:
            file_library: The pathname for all library files.
            file_search: The .msp file which contains spectra to search.
            path_output: The result file.
            ms2_da or ms2_ppm
            method: the name for similarity
    """
    # Read spectral library.
    print("Reading spectral library...")
    spec_library = _read_spectral_library(parameter)
    if search_type == "identity":
        func_search = _identity_search_library
    elif search_type == "hybrid":
        func_search = _hybrid_search_library
        if "ms2_da" not in parameter["search"]:
            parameter["search"]["ms2_da"] = parameter["search"]["ms2_ppm"] * 50 * 1e-6
        spec_library.add_index_for_hybrid_search(parameter["search"]["ms2_da"])
    else:
        raise RuntimeError("search_type error")

    # Score
    similarity_result = parameter["file_output"]
    similarity_result.set_library_information(spec_library.information)
    spec_id = 0
    print("Start score: ", datetime.datetime.now())

    """
    parallel = multiplecore.MPRunner(func_run=func_search,
                                     func_merge=_merge_result,
                                     para_share=(spec_library, parameter["search"]),
                                     para_merge=(similarity_result,),
                                     copy_shared_para=False,
                                     threads=parameter.get("threads", 1))
    # """
    result_all = []
    for spec_search_info in parameter["file_search"].read_one_spectrum(ms2_only=True):
        spec_search_info["precursor_charge"] = parameter["charge"]
        SpectraCollector.standardize_query_spectrum(spec_search_info)
        spec_query = {"scan_number": spec_search_info["scan_number"],
                      "name": spec_search_info["name"],
                      "id": spec_search_info["id"],
                      "precursor_mz": spec_search_info["precursor_mz"],
                      "adduct": spec_search_info["adduct"],
                      "peaks": spec_search_info["peaks"]}
        if spec_query["precursor_mz"] is not None and \
                len(spec_query["adduct"]) > 0 and \
                (spec_query["adduct"][-1] == "+" or spec_query["adduct"][-1] == "-") and \
                len(spec_query["peaks"]) > 0:
            # Add the information
            new_s = {}
            for i in spec_query:
                if i != "peaks":
                    new_s["query_" + i] = spec_query[i]
            similarity_result.add_query_information(spec_query["scan_number"], new_s)
            cur_result = func_search(spec_query, spec_library, parameter["search"])
            if cur_result:
                similarity_result.add_result_list(cur_result)

            #result_all.append(func_search(spec_query, spec_library, para))
            #parallel.add_parameter_for_job((spec_query,), debug=0)
            if spec_id % 1000 == 0:
                print("{} spectra have been processed.".format(spec_id))
            spec_id += 1

    print("Total find {} spectra.".format(spec_id))
    #result_all = parallel.get_result()

    # Output result
    similarity_result.finish_output()
    print("Finished: ", datetime.datetime.now())


def _hybrid_search_library(spec_search_info, spec_library, para):
    # print(spec_search_info["spectrum_id"])
    result = []

    precursor_mz, adduct, peaks = \
        spec_search_info["precursor_mz"], spec_search_info["adduct"], \
        np.asarray(spec_search_info.pop("peaks"), dtype=np.float32, order="C")

    # Add noise, the m/z for noise will be higher than precursor m/z.
    if para["clean_spectra"]:
        peaks_search = tool.preprocess_peaks(
            precursor_mz, peaks, para["noise"], para["precursor_removal"],
            ms2_da=para.get("ms2_da", None), ms2_ppm=para.get("ms2_ppm", None)
        )
    else:
        peaks_search = peaks

    spec_candidate_info_all = spec_library.get_candidate_spectra_for_hybrid_search(
        precursor_mz=precursor_mz,
        precursor_type=adduct,
        peaks=peaks_search,
        ms2_da=para["ms2_da"]
    )
    if len(spec_candidate_info_all) == 0:
        return result
    # print("Find {} spectra.".format(len(spec_candidate_info_all)))
    # Calculate similarity score
    for spec_candidate_info in spec_candidate_info_all:
        similarity = hybrid_similarity.similarity(peaks_search, spec_candidate_info[1],
                                                  precursor_mz - spec_candidate_info[0],
                                                  ms2_ppm=para.get("ms2_ppm", None),
                                                  ms2_da=para.get("ms2_da", None),
                                                  need_clean_spectra=False)
        if similarity >= para["score_min"]:
            result.append([spec_search_info["scan_number"], spec_candidate_info[-1], similarity])

    return result


def _identity_search_library(spec_search_info, spec_library, para):
    # print(spec_search_info["spectrum_id"])
    result = []

    precursor_mz, adduct, peaks = \
        spec_search_info["precursor_mz"], spec_search_info["adduct"], \
        np.asarray(spec_search_info.pop("peaks"), dtype=np.float32, order="C")

    spec_candidate_info_all = spec_library.get_candidate_spectra(
        precursor_mz=precursor_mz,
        adduct=adduct,
        delta_da=para.get("ms1_da", None), delta_ppm=para.get("ms1_ppm", None)
    )
    if len(spec_candidate_info_all) == 0:
        return result

    if para["clean_spectra"]:
        spec_search = tool.preprocess_peaks(precursor_mz, peaks, para["noise"], para["precursor_removal"],
                                            ms2_da=para.get("ms2_da", None), ms2_ppm=para.get("ms2_ppm", None))
    else:
        spec_search = peaks

    # Calculate similarity score
    for spec_candidate_info in spec_candidate_info_all:
        similarity = spectral_similarity_simple.entropy_similarity(spec_search,
                                                                   spec_candidate_info[1],
                                                                   ms2_ppm=para.get("ms2_ppm", None),
                                                                   ms2_da=para.get("ms2_da", None),
                                                                   need_clean_spectra=False)
        if similarity >= para["score_min"]:
            result.append([spec_search_info["scan_number"], spec_candidate_info[-1], similarity])
        result.sort(key=lambda x: -x[-1])

    return result
