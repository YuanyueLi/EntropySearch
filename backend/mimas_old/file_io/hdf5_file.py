import numpy as np
import os
import logging


def read_one_spectrum(filename_input):
    import h5py
    """
    Read information from .hdf5 file.
    :param filename_input: a .hdf5 file.
    :return: a dict contains a list with key 'spectra'.
        The list contains multiple dict, one dict represent a single spectrum's informaiton.
    """
    file = h5py.File(filename_input, "r")

    ms2_len = len(file["Raw"]["MS2_scans"]['mono_mzs2'])

    for ms_id in range(ms2_len):
        idx_start = file["Raw"]["MS2_scans"]['indices_ms2'][ms_id]
        idx_end = file["Raw"]["MS2_scans"]['indices_ms2'][ms_id + 1]
        intensity = file["Raw"]["MS2_scans"]['int_list_ms2'][idx_start:idx_end]
        mz = file["Raw"]["MS2_scans"]['mass_list_ms2'][idx_start:idx_end]
        precursor_mz = file["Raw"]["MS2_scans"]['mono_mzs2'][ms_id]
        rt = file["Raw"]["MS2_scans"]['rt_list_ms2'][ms_id]
        scan_num = file["Raw"]["MS2_scans"]['scan_list_ms2'][ms_id]
        charge = file["Raw"]["MS2_scans"]['charge2'][ms_id]
        peak = np.ascontiguousarray(np.array([mz, intensity]).T)

        spec = {
            "ms_level": 2,
            '_scan_number': scan_num,
            'rt': rt,
            'precursor_mz': precursor_mz,
            'precursor_charge': charge,
            "peaks": peak
        }
        yield spec


class AlphaPept:
    def __init__(self):
        import alphapept.io
        self._file_hdf5: str = None
        self.file: alphapept.io.MS_Data_File = None

    def get_feature_ms2(self):
        ms_features = self.file.read(dataset_name="features")
        query_data = self.file.read_DDA_query_data()
        ms_features["scan"] = -1
        for i, row in ms_features.iterrows():
            ms_features.at[i, "scan"] = query_data["scan_list_ms2"][int(row["query_idx"])]
        return ms_features

    def get_feature_ms1(self):
        ms_feature_table = self.file.read(dataset_name="feature_table")
        return ms_feature_table

    def get_spectra(self):
        query_data = self.file.read_DDA_query_data()
        return query_data

    def read_file(self, file_hdf5=None, file_raw=None):
        import alphapept.io

        if file_hdf5 is None:
            file_hdf5 = os.path.splitext(file_raw)[0] + ".ms_data.hdf"

        self._file_hdf5 = file_hdf5
        self.file = alphapept.io.MS_Data_File(file_hdf5, is_new_file=False)

    def process_file_from_raw(self, file_raw=None, file_hdf5=None, settings: dict = None):
        import alphapept.io
        from alphapept.feature_finding import extract_hills, split_hills, filter_hills, get_hill_data, \
            get_pre_isotope_patterns, maximum_offset, get_isotope_patterns, feature_finder_report, extract_bruker, \
            convert_bruker, map_ms2
        from alphapept.constants import averagine_aa, isotopes

        self._file_hdf5 = file_hdf5
        if self._file_hdf5 is None:
            self._file_hdf5 = os.path.splitext(file_raw)[0] + ".ms_data.hdf"

        f_settings = {
            "max_gap": 2,
            "centroid_tol": 8,
            "hill_length_min": 3,
            "hill_split_level": 1.3,
            "iso_split_level": 1.3,
            "hill_smoothing": 1,
            "hill_check_large": 40,
            "iso_charge_min": 1,
            "iso_charge_max": 6,
            "iso_n_seeds": 100,
            "hill_nboot_max": 300,
            "hill_nboot": 150,
            "iso_mass_range": 5,
            "iso_corr_min": 0.6,
            "map_mz_range": 0.05,
            "map_rt_range": 0.5,
            "map_mob_range": 0.3,
            "map_n_neighbors": 5,
            "search_unidentified": True
        }
        if settings is not None:
            f_settings.update(settings)

        base, ext = os.path.splitext(file_raw)

        if ext.lower() == '.raw':
            datatype = 'thermo'
        elif ext.lower() == '.d':
            datatype = 'bruker'
        elif ext.lower() == '.mzml':
            datatype = 'mzml'
        else:
            raise NotImplementedError('File extension {} not understood.'.format(ext))

        self.file = alphapept.io.MS_Data_File(self._file_hdf5, is_new_file=True)
        self.file.import_raw_DDA_data(file_raw, n_most_abundant=-1)
        query_data = self.file.read_DDA_query_data()

        # if 1:
        if datatype in ['thermo', 'mzml']:

            max_gap = f_settings['max_gap']
            centroid_tol = f_settings['centroid_tol']
            hill_split_level = f_settings['hill_split_level']
            iso_split_level = f_settings['iso_split_level']

            window = f_settings['hill_smoothing']
            hill_check_large = f_settings['hill_check_large']

            iso_charge_min = f_settings['iso_charge_min']
            iso_charge_max = f_settings['iso_charge_max']
            iso_n_seeds = f_settings['iso_n_seeds']

            hill_nboot_max = f_settings['hill_nboot_max']
            hill_nboot = f_settings['hill_nboot']

            iso_mass_range = f_settings['iso_mass_range']

            iso_corr_min = f_settings['iso_corr_min']

            logging.info('Feature finding on {}'.format(file_raw))

            logging.info(f'Hill extraction with centroid_tol {centroid_tol} and max_gap {max_gap}')

            hill_ptrs, hill_data, path_node_cnt, score_median, score_std = extract_hills(query_data, max_gap,
                                                                                         centroid_tol)
            logging.info(f'Number of hills {len(hill_ptrs):,}, len = {np.mean(path_node_cnt):.2f}')

            logging.info(f'Repeating hill extraction with centroid_tol {score_median + score_std * 3:.2f}')

            hill_ptrs, hill_data, path_node_cnt, score_median, score_std = extract_hills(query_data, max_gap,
                                                                                         score_median + score_std * 3)
            logging.info(f'Number of hills {len(hill_ptrs):,}, len = {np.mean(path_node_cnt):.2f}')

            int_data = np.array(query_data['int_list_ms1'])

            hill_ptrs = split_hills(hill_ptrs, hill_data, int_data, hill_split_level=hill_split_level,
                                    window=window)  # hill lenght is inthere already
            logging.info(f'After split hill_ptrs {len(hill_ptrs):,}')

            hill_data, hill_ptrs = filter_hills(hill_data, hill_ptrs, int_data,
                                                hill_check_large=hill_check_large, window=window)

            logging.info(f'After filter hill_ptrs {len(hill_ptrs):,}')

            stats, sortindex_, idxs_upper, scan_idx, hill_data, hill_ptrs = get_hill_data(query_data, hill_ptrs,
                                                                                          hill_data,
                                                                                          hill_nboot_max=hill_nboot_max,
                                                                                          hill_nboot=hill_nboot)
            logging.info('Extracting hill stats complete')

            pre_isotope_patterns = get_pre_isotope_patterns(stats, idxs_upper, sortindex_, hill_ptrs, hill_data,
                                                            int_data, scan_idx, maximum_offset,
                                                            iso_charge_min=iso_charge_min,
                                                            iso_charge_max=iso_charge_max,
                                                            iso_mass_range=iso_mass_range,
                                                            cc_cutoff=iso_corr_min)
            logging.info('Found {:,} pre isotope patterns.'.format(len(pre_isotope_patterns)))

            isotope_patterns, iso_idx, isotope_charges = get_isotope_patterns(pre_isotope_patterns, hill_ptrs,
                                                                              hill_data, int_data, scan_idx,
                                                                              stats, sortindex_, averagine_aa,
                                                                              isotopes,
                                                                              iso_charge_min=iso_charge_min,
                                                                              iso_charge_max=iso_charge_max,
                                                                              iso_mass_range=iso_mass_range,
                                                                              iso_n_seeds=iso_n_seeds,
                                                                              cc_cutoff=iso_corr_min,
                                                                              iso_split_level=iso_split_level,
                                                                              callback=None)
            logging.info('Extracted {:,} isotope patterns.'.format(len(isotope_charges)))

            feature_table = feature_finder_report(query_data, isotope_patterns, isotope_charges, iso_idx, stats,
                                                  sortindex_, hill_ptrs, hill_data)

            logging.info('Report complete.')

        elif datatype == 'bruker':
            logging.info('Feature finding on {}'.format(file_raw))
            feature_path = extract_bruker(file_raw)
            feature_table = convert_bruker(feature_path)
            logging.info('Bruker featurer finder complete. Extracted {:,} features.'.format(len(feature_table)))
        else:
            raise NotImplementedError()

        # Calculate additional params
        feature_table['rt_length'] = feature_table['rt_end'] - feature_table['rt_start']
        feature_table['rt_right'] = feature_table['rt_end'] - feature_table['rt_apex']
        feature_table['rt_left'] = feature_table['rt_apex'] - feature_table['rt_start']
        feature_table['rt_tail'] = feature_table['rt_right'] / feature_table['rt_left']

        logging.info('Matching features to query data.')
        features = map_ms2(feature_table, query_data, **f_settings)

        #################################################
        # Modified from origin
        # Filter map result by m/z.
        mass_check = np.abs(features['mz_offset'].values) <= f_settings["map_mz_range"]
        features = features[mass_check]

        # For every MS2, only one feature is selected.
        features = features.sort_values(by='mz_offset', key=abs)
        features = features.drop_duplicates(subset=['query_idx'])

        logging.info('Saving feature table.')
        self.file.write(feature_table, dataset_name="feature_table")
        logging.info('Feature table saved to {}'.format(self._file_hdf5))

        logging.info('Saving features.')
        self.file.write(features, dataset_name="features")
        logging.info(f'Feature finding of file {file_raw} complete.')
