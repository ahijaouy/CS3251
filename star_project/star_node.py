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
    NO_CONTACT_TIMEOUT = 60 * 3  # 3 minutes

    def __init__(self, name, port, num_nodes, host=None, poc_name=None, poc_ip=None, poc_port=None, verbose=False):

        self.name = name
        self.port = port
        self.num_nodes = num_nodes

        self.central_node = None
        self.poc = self.set_poc(poc_name, poc_ip, poc_port)
        self.socket_manager = SocketManager(
            name, port, host, self.report, verbose)
        self.address = self.socket_manager.get_address()
        self.directory = {}
        self.directory[name] = ContactNode(
            name=name,
            ip=self.address[0],
            port=self.address[1]
        )
        self.log = Logger(name, verbose=True)
        self.last_contacted = time.time()

    def report(self):
        self.last_contacted = time.time()

    def start_non_blocking(self):
        start_thread = Thread(target=self.start)
        start_thread.start()

    def start(self):
        self.socket_manager.start()
        self.log.debug("Socket Started Successfully")

        self.try_to_contact_poc()
        # self.start_heartbeat()
        # self.start_rtt_calculations()
        self.check_for_new_messages()
        # self.check_for_user_input()

        while True:  # Blocking. Nothing can go below this
            self.check_for_inactivity()

    def check_for_new_messages(self):
        discovery_thread = Thread(target=self.watch_for_discovery_messages)
        discovery_thread.start()

    def watch_for_discovery_messages(self):
        print(">>>>>>>>>>>")
        while True:
            message = self.socket_manager.get_discovery_message()
            if message.direction == "0":
                print("========")
                self.handle_discovery_message(message)
                self.log.debug(
                    f'Handled Discovery Message from {message.origin_address}')
            else:
                self.socket_manager.return_discovery_message(message)

    # def check_for_user_input(self):
    #     pass

    def check_for_inactivity(self):
        """ 
        Monitors when the node was last active. 

        If node has been inactive (recieved no packets) for more than 
        3 minutes (NO_CONTACT_TIMEOUT) then terminated program
        """
        if self.last_contacted + self.NO_CONTACT_TIMEOUT < time.time():
            import sys
            sys.exit("StarNode terminated due to inactivity with other nodes")

    def ensure_sender_is_known(self, message):
        # TODO: Messages should include sender's name
        # TODO: Check if message's sender is in self.dictionary or send discovery request
        pass

    def handle_discovery_message(self, message):
        # TODO Should make sure if message origin is not already in this node's Dict
        # then we should send a Discovery message to the origin node.
        resp_msg = MessageFactory.generate_discovery_message(
            origin=self.address,
            destination=message.origin_address,
            direction="1",
            payload=self._serialize_directory())
        self.socket_manager.send_message(resp_msg)
        self.ensure_sender_is_known(message)

    # def send_heartbeat(self):
    #     while True:
    #         self.log.debug("Sending Heartbeat")

    #         time.sleep(self.HEARTBEAT_TIMEOUT)

    # def start_heartbeat(self):
    #     heartbeat_thread = Thread(target=self.send_heartbeat, daemon=True)
    #     heartbeat_thread.start()

    # def send_rtt(self):
    #     while True:
    #         self.log.debug("Sending RTT")
    #         time.sleep(self.RTT_TIMEOUT)

    # def start_rtt_calculations(self):
    #     rtt_thread = Thread(target=self.send_rtt, daemon=True)
    #     rtt_thread.start()

    def set_poc(self, name, ip, port):
        poc = None
        if name != None:
            poc = ContactNode(name, ip, port)
            # self.directory[name] = poc
        return poc

    def _serialize_directory(self):
        directory = []

        for key in self.directory:
            directory.append(self.directory[key].to_json())
        return json.dumps(directory)

    def _deserialize_into_directory(self, serialized):
        deserialized = json.loads(serialized)
        directory = {}
        for node_json in deserialized:
            node = ContactNode.create_from_json(node_json)
            directory[node.name] = node
        return directory

    def _merge_into_directory(self, json_dict):
        for key in json_dict:
            self.directory[key] = json_dict[key]
        self.log.debug(
            f'Added {len(json_dict)} entries to Directory (new size={len(self.directory)})')

    def broadcast(self, data, dests):
        pass

    def try_to_contact_poc(self):
        # TODO If successfully reaches POC add to Directory
        if self.poc != None:
            poc_thread = Thread(target=self.contact_poc, daemon=True)
            poc_thread.start()
            self.log.debug("Started Thread to contact POC")

    def contact_poc(self):
        # Generate and send Discovery Message
        discovery_message = MessageFactory.generate_discovery_message(
            origin=self.address,
            destination=(self.poc.ip, self.poc.port)
        )
        self.socket_manager.send_message(discovery_message)
        self.log.debug("Attempted to contact POC Node")
        # Wait for response
        while self.directory.get(self.poc.name, None) == None:
            discovery_resp = self.socket_manager.get_discovery_message()
            # print(discovery_resp.direction)
            # print(discovery_resp.payload)
            # print(discovery_resp.origin_address)
            # print(discovery_resp.destination_address)

            # import pdb
            # pdb.set_trace()
            if discovery_resp.is_response_to(discovery_message):
                print("!>!@>#!@#!@$!@#$")
                directory = self._deserialize_into_directory(
                    discovery_resp.payload)
                self._merge_into_directory(directory)
            else:
                self.socket_manager.return_discovery_message(discovery_resp)
        self.log.debug("Response from POC successfully recieved.")
