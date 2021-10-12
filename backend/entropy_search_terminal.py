from mimas.helper.arguments import Arguments
from mimas.spectra.library_search.untarget_search import untarget_search
from mimas.spectra.library_search.target_search import target_search
from mimas.spectra.library_search.file_adaptor import AdaptorSpecFile, AdaptorIndexFile, AdaptorSimilarityResult


def main(para):
    """
    Common parameter: {
        "threads": 1,
        "precursor_removal": 1.6,
        "ms2_da": 0.05,
        "noise": 0.01,
        "score_min": 0.5,
    }
    """
    # Pre-process
    para["search"] = {}
    for item in ["score_min", "result_max", "ms1_ppm", "ms1_da", "ms2_ppm", "ms2_da", "shift",
                 "clean_spectra", "precursor_removal", "noise"]:
        if item in para:
            para["search"][item] = para[item]
    para["file_output"] = AdaptorSimilarityResult(para["file_output"], ".csv")
    para["file_search"] = AdaptorSpecFile(para["file_search"])
    para["file_library"] = [[AdaptorSpecFile(para["file_library"]), AdaptorIndexFile(para["file_library"] + ".index")]]

    # Run search
    if para["method"] == "untarget-identity":
        """
        search parameter: {
            "method": "target-identity",
            "ms1_ppm": 10,
        }
        """
        untarget_search(search_type="identity", parameter=para)

    elif para["method"] == "untarget-hybrid":
        """
        search parameter: {
            "method": "target-hybrid",
        }
        """
        untarget_search(search_type="hybrid", parameter=para)

    elif para["method"] == "target-shift":
        """
        search parameter: {
            "method": "target-shift",
            "shift": 162.0533
        }
        """
        target_search(search_type="shift", parameter=para)


if __name__ == '__main__':
    args = Arguments()
    para_shared = {
        "threads": 7,
        "precursor_removal": 1.6,
        "ms2_da": 0.05,
        "score_min": 0.5,
        "noise": 0.01,
        "clean_spectra": True,

        'file_search': r"D:\test\db\test.msp",
        "file_library": r"D:\test\db\test.msp",
        'file_output': r"D:\test\db\test.csv",
    }
    para_untarget_hybrid = {
        "method": "untarget-hybrid",
    }
    para_untarget_identity = {
        "method": "untarget-identity",
        "ms1_ppm": 10,
    }
    para_target_shift = {
        "method": "target-shift",
        "shift": 162.0533,
    }

    para = para_shared
    para.update(para_untarget_identity)
    args.add_parameter(para)

    para = args.parse_args()

    # Check parameter
    para["ms1_da"] = para.get("ms1_da", None)
    if para["ms1_da"] is not None:
        para["ms1_da"] = float(para["ms1_da"])
        para["ms1_ppm"] = None
    else:
        para["ms1_ppm"] = float(para.get("ms1_ppm", 10.))

    para["ms2_ppm"] = para.get("ms2_ppm", None)
    if para["ms2_ppm"] is not None:
        para["ms2_ppm"] = float(para["ms2_ppm"])
        para["ms2_da"] = None
    else:
        para["ms2_da"] = float(para.get("ms2_da", 0.05))

    para["precursor_removal"] = float(para.get("precursor_removal", 1.6))
    para["noise"] = float(para.get("noise", 0.01))
    para["score_method"] = para.get("score_method", "entropy")

    main(para)
