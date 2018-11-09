#!/usr/bin/env python3
"""
Logger

Provides Basic Logging functions in a single place.
"""
from time import gmtime, strftime


class Logger():
    def __init__(self, name, verbose=False):
        self.name = name
        self.verbose = verbose
        self.log_file_name = f'{name}-log.log'

    def debug(self, text):
        if self.verbose:
            print(f'{self.name}: ', text)

    def error(self, text, err):
        if self.verbose:
            print(f'ERROR {self.name}:  ', text, e)

    def clear_log(self):
        with open(self.log_file_name, "w+") as f:
            f.write(f'------------- {self.name} ACTIVITY LOG -------------\n')

    def write_to_log(self, message_type, text):
        with open(self.log_file_name, 'a+') as f:
            time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            message = f'{time} | {message_type} -- {text}\n'
            f.write(message)

    def print_log(self):
        with open(self.log_file_name, "r") as f:
            contents = f.read()
            print(contents)
