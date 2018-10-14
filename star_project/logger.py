#!/usr/bin/env python3
"""
Logger

Provides Basic Logging functions in a single place.
"""


class Logger():
    def __init__(self, name, verbose=False):
        self.name = name
        self.verbose = verbose

    def debug(self, text):
        if self.verbose:
            print(f'{self.name}: ', text)

    def error(self, text, err):
        if self.verbose:
            print(f'ERROR {self.name}:  ', text, e)

    def write_to_log(self, text):
        pass  # TODO Implement
