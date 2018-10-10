#!/usr/bin/env python3
"""
StarNet Node

1. Upon startup attempt to contact POC if one is given
2. Heartbeat Thread starts trying to reach Contact Nodes
3. RTT Thread starts calculating RTT
"""

import argparse
import socket
import time
import json
from threading import Thread

from contact_node import ContactNode
from socket_manager import SocketManager
from message_factory import MessageFactory, DiscoveryMessage
from logger import Logger


class StarNode():
    HEARTBEAT_TIMEOUT = 5  # seconds
    RTT_TIMEOUT = 5  # seconds

    def __init__(self, name, port, num_nodes, host=None, poc_name=None, poc_ip=None, poc_port=None, verbose=False):
        self.name = name
        self.port = port
        self.num_nodes = num_nodes
        self.directory = {}
        self.central_node = None
        self.poc = self.set_poc(poc_name, poc_ip, poc_port)
        self.socket_manager = SocketManager(name, port, host, verbose)
        self.log = Logger(name, verbose=True)

    def start(self):
        self.socket_manager.start()
        self.log.debug("Socket Started Successfully")

        self.try_to_contact_poc()
        # self.start_heartbeat()
        # self.start_rtt_calculations()

    def send_heartbeat(self):
        while True:
            self.log.debug("Sending Heartbeat")

            time.sleep(self.HEARTBEAT_TIMEOUT)

    def start_heartbeat(self):
        heartbeat_thread = Thread(target=self.send_heartbeat)
        heartbeat_thread.start()

    def send_rtt(self):
        while True:
            self.log.debug("Sending RTT")
            time.sleep(self.RTT_TIMEOUT)

    def start_rtt_calculations(self):
        rtt_thread = Thread(target=self.send_rtt)
        rtt_thread.start()

    def set_poc(self, name, ip, port):
        poc = None
        if name != None:
            poc = ContactNode(name, ip, port)
            self.directory[name] = poc
        return poc

    def _serialize_directory(self):
        directory = []
        for key in self.directory:
            directory.push(self.directory[key].to_json())
        return json.dumps(directory)

    def _deserialize_directory(self, serialized):
        deserialized = json.loads(serialized)
        directory = []
        for node_json in deserialized:
            directory.push(ContactNode.create_from_json(node_json))
        return directory

    def _merge_into_directory(directory):
        for key in directory:
            self.directory[key] = directory[key]

    def broadcast(self, data, dests):
        pass

    def try_to_contact_poc(self):
        if self.poc != None:
            poc_thread = Thread(target=self.contact_poc)
            poc_thread.start()
            self.log.debug("Started Thread to contact POC")

    def contact_poc(self):
        # TODO Should try to contact POC repeatedly until a response is resieved

        address = (self.poc.ip, self.poc.port)

        discovery_message = MessageFactory.generate_discovery_message(
            address)

        self.socket_manager.send_message(discovery_message)
