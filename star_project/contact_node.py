#!/usr/bin/env python3
"""
Contact Node

Stores information about a Contact Node in the StarNet.
"""

import json


class ContactNode():

    def __init__(self, **kwargs):
        self.name = kwargs.get('name', None)
        self.ip = kwargs.get('ip', None)
        self.port = int(kwargs.get('port', None))
        self.rtt = None

    @classmethod
    def create_from_json(cls, raw_json):
        "returns a new instance of ContactNode from json"
        data = json.loads(raw_json)
        return cls(name=data["name"], ip=data["ip"], port=data["port"])

    def to_json(self):
        "serializes current object to json"
        return json.dumps({
            "name": self.name,
            "ip": self.ip,
            "port": self.port
        })
