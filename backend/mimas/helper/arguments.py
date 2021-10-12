import argparse
import datetime
import json
import os
import pprint
import sys
import logging
import pathlib


class Arguments(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super(Arguments, self).__init__(add_help=True, *args, **kwargs)
        self.formatter_class = argparse.RawTextHelpFormatter

        self.parameter: dict = {
            'threads': None
        }

        self.add_argument('-para', type=str)
        self.add_argument('-threads', type=int)
        self.add_argument('-debug', type=int)
        self.add_argument('-path_output', type=str)
        self.add_argument('-output_parameter', type=bool)

    def add_parameter(self, para: dict) -> None:
        """"
        Over current parameter
        """

        for item in para:
            if "-" + item not in self._option_string_actions:
                if isinstance(para[item],list):
                    self.add_argument("-" + item, nargs='*')
                else:
                    self.add_argument("-" + item, type=type(para[item]))

        self.parameter.update(para)

    def add_argument_by_example(self, para: dict):
        self.set_defaults(**para)

    def parse_args(self, args=None, namespace=None):
        # Parameter order:
        # CMD input > json file > default
        # parameters_args_cmd_input > parameters_args_cmd_input["para"] > self.parameter
        parameters_args_cmd_input = vars(super(Arguments, self).parse_args(args))
        parameters_args_cmd_input = {k: parameters_args_cmd_input[k]
                                     for k in parameters_args_cmd_input if parameters_args_cmd_input[k] is not None}

        # Parameter from json file
        if parameters_args_cmd_input.get("para", None) is not None:
            parameters_json = json.load(open(parameters_args_cmd_input["para"], "rt"))
            if "para" in parameters_json:
                parameters_json.pop("para")

            # Merge parameters
            parameters_json.update(parameters_args_cmd_input)
            self.parameter.update(parameters_json)
        else:
            # Merge parameters
            self.parameter.update(parameters_args_cmd_input)

        # Fill default parameter
        if 'threads' not in self.parameter:
            self.parameter["threads"] = 1
        if 'output_parameter' not in self.parameter:
            self.parameter["output_parameter"] = False
        if 'path_output' not in self.parameter:
            self.parameter['path_output'] = ""

        # If path_output is not defined, guess it.
        if not self.parameter['path_output']:
            if 'file_output' in self.parameter and self.parameter['file_output']:
                self.parameter['path_output'] = os.path.dirname(self.parameter['file_output'])
            elif 'path_input' in self.parameter and self.parameter['path_input']:
                self.parameter['path_output'] = os.path.dirname(self.parameter['path_input'])
            elif 'file_input' in self.parameter and self.parameter['file_input']:
                self.parameter['path_output'] = os.path.dirname(self.parameter['file_input'])

        # Convert to absolute path.
        if not os.path.isabs(self.parameter['path_output']):
            self.parameter['path_output'] = \
                os.path.join(os.getcwd(), self.parameter['path_output'])

        # Fix path name
        if self.parameter["path_output"]:
            self.parameter["path_output"] = pathlib.Path(self.parameter["path_output"])
        if self.parameter.get("path_input", ""):
            self.parameter["path_input"] = pathlib.Path(self.parameter["path_input"])

        # Create path is not existed.
        if not os.path.exists(self.parameter['path_output']):
            os.makedirs(self.parameter['path_output'])

        # Add parameter file in output path
        log_output = os.path.join(self.parameter["path_output"],
                                  "parameter-" + datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + '.log')
        if self.parameter["output_parameter"]:
            logging.basicConfig(filename=log_output, level=logging.DEBUG, format='%(asctime)s %(message)s')
            logging.debug(pprint.pformat(self.parameter))

        pprint.pprint(self.parameter)
        return self.parameter
