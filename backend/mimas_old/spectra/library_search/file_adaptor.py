import pickle
import pandas as pd
from mimas.file_io import spec_file


class AdaptorSimilarityResult:
    def __init__(self, output_target, output_type=".csv"):
        self.output_target = open(output_target, "wt", encoding='utf-8')
        self.output_type = output_type

        self.query_information = {}
        self.library_information = {}
        self.output_header = None

    def add_query_information(self, scan_number, information):
        self.query_information[scan_number] = information

    def set_library_information(self, information):
        self.library_information = information

    def add_result_list(self, result_list):
        result_final = []
        if result_list:
            for query_id, library_id, score in result_list:
                result_cur = {}
                result_cur.update(self.query_information[query_id])
                result_cur.update(self.library_information[library_id])
                result_cur["score"] = score
                result_final.append(result_cur)

        if result_final:
            df = pd.DataFrame(result_final)
            if self.output_header is None:
                self.output_header = list(result_final[0].keys())
                output_string = df.to_csv(columns=self.output_header, index=False, header=True, line_terminator="\n")
            else:
                output_string = df.to_csv(columns=self.output_header, index=False, header=False, line_terminator="\n")
            # print(output_string)
            self.output_target.writelines(output_string)

    def finish_output(self):
        self.output_target.close()


class AdaptorSpecFile:
    def __init__(self, filename):
        self.filename = filename

    def get_filename(self):
        return self.filename

    def read_one_spectrum(self, ms2_only=True, **kwargs: object):
        for spec in spec_file.read_one_spectrum(self.filename, ms2_only=True):
            yield spec


class AdaptorIndexFile:
    def __init__(self, filename):
        self.filename = filename

    def save_data(self, data):
        pickle.dump(data, open(self.filename, "wb"))

    def load_data(self):
        return pickle.load(open(self.filename, "rb"))
