import numpy as np
import pandas as pd
import datetime

from mimas.database.spectra_collector import SpectraCollector
from mimas.file_io import spec_file
from mimas.helper import multiplecore
from mimas.spectra.similarity import hybrid_similarity
from . import tool


def _read_spectral_library(para):
    spec_library = SpectraCollector()
    spec_library.read_spectra_file(para["file_library"])
    spec_library.preprocess_peaks(tool.preprocess_peaks, para["threads"],
                                  para["noise"], para["precursor_removal"],
                                  para.get("ms2_da", None), para.get("ms2_ppm", None))
    return spec_library


def _shift_search_library(spec_search_info, spec_library, para):
    # print(spec_search_info["spectrum_id"])
    result = []

    precursor_mz, adduct, peaks = \
        spec_search_info["precursor_mz"], spec_search_info["adduct"], \
        np.asarray(spec_search_info.pop("peaks"), dtype=np.float32, order="C")

    spec_candidate_info_all_1 = spec_library.get_candidate_spectra(
        precursor_mz=precursor_mz,
        adduct=adduct,
        delta_da=para["ms1_da"], delta_ppm=para["ms1_ppm"]
    )
    spec_candidate_info_all_2 = spec_library.get_candidate_spectra(
        precursor_mz=precursor_mz - para["shift"],
        adduct=adduct,
        delta_da=para["ms1_da"], delta_ppm=para["ms1_ppm"]
    )
    spec_candidate_info_all = spec_candidate_info_all_1 + spec_candidate_info_all_2
    if len(spec_candidate_info_all) == 0:
        return result

    # Add noise, the m/z for noise will be higher than precursor m/z.
    peaks_search = tool.preprocess_peaks(
        precursor_mz, peaks, para["noise"], para["precursor_removal"],
        ms2_da=para["ms2_da"], ms2_ppm=para["ms2_ppm"]
    )

    # print("Find {} spectra.".format(len(spec_candidate_info_all)))
    # Calculate similarity score
    for spec_candidate_info in spec_candidate_info_all:
        similarity = hybrid_similarity.similarity(peaks_search, spec_candidate_info[1],
                                                  precursor_mz - spec_candidate_info[0],
                                                  ms2_ppm=para["ms2_ppm"],
                                                  ms2_da=para["ms2_da"],
                                                  need_clean_spectra=False)
        if similarity >= para["score_min"]:
            result.append([spec_search_info["scan_number"], spec_candidate_info[-1], similarity])

    return result


def target_search(search_type, parameter):
    """
    :param search_type: "shift"
    :param parameter: the following fields are required:
            file_library: The pathname for all library files.
            file_search: The .msp file which contains spectra to search.
            path_output: The result file.
            ms2_da or ms2_ppm
            method: the name for similarity
    """
    # Read spectral library.
    spec_library = _read_spectral_library(parameter)
    if search_type == "shift":
        if "ms2_da" not in parameter:
            parameter["ms2_da"] = parameter["ms2_ppm"] * 50 * 1e-6
        spec_library.add_index_for_hybrid_search(parameter["ms2_da"])
        func_search = _shift_search_library
    else:
        raise RuntimeError("search_type error")

    # Score
    fo = open(parameter["file_output"], "wt", encoding='utf-8')
    spec_id = 0
    spec_search_info_all = {}
    print("Start score: ", datetime.datetime.now())

    # """
    parallel = multiplecore.MPRunner(func_run=func_search,
                                     func_merge=_merge_result,
                                     para_share=(spec_library, parameter),
                                     para_merge=(spec_search_info_all, spec_library, fo,),
                                     copy_shared_para=False,
                                     threads=parameter.get("threads", 1))
    # """
    result_all = []
    for spec_search_info in spec_file.read_one_spectrum(parameter["file_search"]):
        SpectraCollector.standardize_query_spectrum(spec_search_info)
        spec_query = {"scan_number": spec_search_info["scan_number"],
                      "name": spec_search_info["name"],
                      "id": spec_search_info["id"],
                      "precursor_mz": spec_search_info["precursor_mz"],
                      "adduct": spec_search_info["adduct"],
                      "peaks": spec_search_info["peaks"],
                      "rt": spec_search_info["rt"]}
        if spec_query["precursor_mz"] is not None and \
                len(spec_query["adduct"]) > 0 and \
                (spec_query["adduct"][-1] == "+" or spec_query["adduct"][-1] == "-") and \
                len(spec_query["peaks"]) > 0:
            # Add the information
            new_s = {}
            for i in spec_query:
                if i != "peaks":
                    new_s["query_" + i] = spec_query[i]
            spec_search_info_all[spec_query["scan_number"]] = new_s

            parallel.add_parameter_for_job((spec_query,), debug=0)
            #result_all.append(func_search(spec_query, spec_library, parameter))
            spec_id += 1

    print("Total find {} spectra.".format(spec_id))
    result_all = parallel.get_result()

    print("Finished: ", datetime.datetime.now())

def _merge_result(pre_information, cur_result, spec_search_info_all, spec_library, fo):
    if cur_result:
        # Add spectral information
        for i, (query_id, library_id, score) in enumerate(cur_result):
            result_cur = {}
            result_cur.update(spec_search_info_all[query_id])
            result_cur.update(spec_library.get_information(library_id))
            result_cur["score"] = score
            cur_result[i] = result_cur

        df = pd.DataFrame.from_dict(cur_result)
        if pre_information is None:
            pre_information = list(cur_result[0].keys())
            output_string = df.to_csv(columns=pre_information, index=False, header=True, line_terminator="\n")

        else:
            output_string = df.to_csv(columns=pre_information, index=False, header=False, line_terminator="\n")
        # print(output_string)
        fo.writelines(output_string)

    return pre_information
