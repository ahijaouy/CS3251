#!/usr/bin/env python3
"""
Contact Node Directory

Stores information about multiple Contact Nodes
"""

import json
import threading
from contact_node import ContactNode
from logger import Logger


class ContactDirectory():

    def __init__(self, name, verbose):
        self.name = name
        self._log = Logger(name, verbose=verbose)
        self.directory = {}
        self.star_node = None
        # self.central_node = None
        # self.central_node_lock = threading.RLock()
        self.lock = threading.RLock()

    def poc_not_added(self, poc):
        for key in self.directory:
            node = self.directory[key]
            if node.ip == poc.ip and node.port == poc.port:
                return False
        return True

    def set_star_node(self, star_node):
        self.star_node = star_node
        # self.add(star_node)

    def size(self):
        with self.lock:
            return len(self.directory)

    def add(self, node):
        with self.lock:
            if node not in self.directory:
                self.directory[node.name] = node

    def get(self, name):
        if name == self.star_node.get_name():
            return self.star_node
        with self.lock:

            try:
                node = self.directory[name]
                if node.is_online:
                    return self.directory[name]
                raise ValueError()
            except KeyError:
                import pdb
                pdb.set_trace()

    def exists(self, name):
        with self.lock:
            return name in self.directory

    def remove(self, name):
        with self.lock:
            self.directory[name].is_online = False

    def get_current_list(self):
        with self.lock:
            copy_dict = {k: v for k, v in self.directory.items()
                         if v.is_online}
            return copy_dict.values()

    def serialize(self):
        """ Serializes the ContactNode Directory to JSON """
        directory = [self.star_node.to_json()]
        with self.lock:
            for key in self.directory:
                if self.directory[key].is_online:
                    directory.append(self.directory[key].to_json())
            return json.dumps(directory)

    def merge_serialized_directory(self, serialized_directory):
        """ Adds an array of serialized ContactNodes to the Directory """
        with self.lock:
            for item in serialized_directory:
                node = ContactNode.create_from_json(item)
                if not (node.name in self.directory) and node.name != self.name:
                    self.directory[node.name] = node
                    self._log.write_to_log(
                        "Discovery", f'{node.name} discovered.')
