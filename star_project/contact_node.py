#!/usr/bin/env python3
"""
Contact Node

Stores information about a Contact Node in the StarNet.
"""

import json
import time


class ContactNode():
    HEARTBEAT_TIMEOUT = 8  # seconds

    def __init__(self, name, ip, port):
        self.name = name
        self.ip = ip
        self.port = port
        self.rtt = None
        self.last_contact = time.time()
        self.is_online = True

    @classmethod
    def create_from_json(cls, raw_json):
        "returns a new instance of ContactNode from json"
        data = json.loads(raw_json)
        return cls(name=data["name"], ip=data["ip"], port=data["port"])

    def get_address(self):
        return (self.ip, self.port)

    def get_16_byte_name(self):
        return format(self.name, '>16')

    def get_name(self):
        return self.name.strip()

    def get_rtt(self):
        return self.rtt

    def to_json(self):
        "serializes current object to json"
        return json.dumps({
            "name": self.name,
            "ip": self.ip,
            "port": self.port
        })

    def is_unresponsive(self):
        return self.last_contact + self.HEARTBEAT_TIMEOUT < time.time()

    def heartbeat(self):
        self.last_contact = time.time()
