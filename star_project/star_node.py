#!/usr/bin/env python3
"""
StarNet Node
"""

import argparse
import socket
import time
import json
from contact_node import ContactNode


class StarNode():

    def __init__(self, **kwargs):
        self.sock = None  # TODO implement
        self.ack_timeout = 1000
        self.POC_NAME = kwargs.get('poc_name', None)
        self.POC_IP = kwargs.get('poc_ip', None)
        self.POC_PORT = int(kwargs.get('poc_port', None))
        self.max_num_nodes = int(kwargs.get('max_num_nodes', None))

        self.directory = {}
        if self.POC_NAME:
            self.contact_poc()

    def serialize_directory(self):
        directory = []
        for key in self.directory:
            directory.push(self.directory[key].to_json())
        return json.dumps(directory)

    def deserialize_directory(self, serialized):
        deserialized = json.loads(serialized)
        directory = []
        for node_json in deserialized:
            directory.push(ContactNode.create_from_json(node_json))
        return directory

    def merge_into_directory(directory):
        for key in directory:
            self.directory[key] = directory[key]

    def _send_packet(self, data, destination):
        """
        Sends UDP Packet
        """
        try:
            sock.sendto(data.encode(), destination)
        except Exception as e:
            print("Exception Occured while sendin packet.\n ", e)

    def send_to(self, data, destination):
        """
        Sends message to destintion and waites for ACK
        """
        confirmed = False

        # while not confirmed:
        start_time = time.time()
        while time.time()-start_time < self.ack_timeout:
            data, address = sock.recvfrom(1024)

    def broadcast(self, data, dests):
        for dest in dests:
            self.send_to(data, dest)

    def connect(self):
        pass

    def contact_poc(self):
        """
        This should probably be done in a thread...
        """
        pass
