#!/usr/bin/env python3
"""
Contact Node Directory

Stores information about multiple Contact Nodes
"""

import json
import copy
import threading
from contact_node import ContactNode


class ContactDirectory():

    def __init__(self):
        self.directory = {}
        self.star_node = None
        self.lock = threading.RLock()

    def set_star_node(self, star_node):
        self.star_node = star_node

    def size(self):
        with self.lock:
            return len(self.directory)

    def add(self, node):
        with self.lock:
            if node not in self.directory:
                self.directory[node.name] = node

    def get(self, name):
        with self.lock:
            if self.directory[name].is_online:
                return self.directory[name]
            raise ValueError()

    def exists(self, name):
        with self.lock:
            return name in self.directory

    def remove(self, name):
        with self.lock:
            self.directory[name].is_online = False

    def get_current_list(self):
        with self.lock:
            copy_dict = copy.deepcopy(self.directory)
            return copy_dict.values()

    def serialize(self):
        """ Serializes the ContactNode Directory to JSON """
        directory = [self.star_node.to_json()]
        with self.lock:
            for key in self.directory:
                directory.append(self.directory[key].to_json())
            return json.dumps(directory)

    def merge_serialized_directory(self, serialized_directory):
        """ Adds an array of serialized ContactNodes to the Directory """
        with self.lock:
            for item in serialized_directory:
                node = ContactNode.create_from_json(item)
                self.directory[node.name] = node
