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
from message_factory import MessageFactory
from logger import Logger


class StarNode():
    # Timeout constants
    HEARTBEAT_TIMEOUT = 5  # seconds
    RTT_TIMEOUT = 5  # seconds
    NO_CONTACT_TIMEOUT = 60 * 3  # 3 minutes

    def __init__(self, name, port, num_nodes, host=None, poc_ip=None, poc_port=None, verbose=False):
        # Initialize instance variables
        self._log = Logger(name, verbose=True)
        self.num_nodes = num_nodes
        self.central_node = None
        self.directory = {}
        if poc_ip != None and poc_port != None:
            self.poc = ContactNode("poc", ip, port)
        else:
            self.poc = None

        # Initialize things related to the socket
        self.socket_manager = SocketManager(
            name, port, host, self.report, verbose)
        self.address = self.socket_manager.get_address()
        self.directory[name] = self.socket_manager.node

    """
    General Control Functions
    """

    def start(self):
        """ Startes the StarNode and kicks off all lifecycle functions"""
        self.socket_manager.start()
        self._log.debug("Socket Started Successfully")

        if self.poc != None:
            self.send_discovery_message(self.poc)
        self._start_daemon_thread(self.watch_for_discovery_messages)

        while True:  # Blocking. Nothing can go below this
            self.check_for_inactivity()

    def start_non_blocking(self):
        """ Allows StarNode to be started without blocking """
        self._start_daemon_thread(self.start)

    def broadcast(self, data, dests):
        """
        Sends a message to all nodes in the network via the Central Node
        """
        pass

    def report(self):
        """ Updates the time a packet was last received """
        self.last_contacted = time.time()

    def check_for_inactivity(self):
        """ 
        Monitors when the node was last active. 

        If node has been inactive (recieved no packets) for more than 
        3 minutes (NO_CONTACT_TIMEOUT) then terminated program
        """
        if self.last_contacted + self.NO_CONTACT_TIMEOUT < time.time():
            import sys
            sys.exit("StarNode terminated due to inactivity with other nodes")

    """
    Peer Discovery Functions

    Handle contacting POC Node, responding to new Discovery Requests, and
    ensuring all incoming requests are from known ContactNodes.
    """

    def watch_for_discovery_messages(self):
        """ Waits and handles all discovery messages that arrive to this node. """
        while True:
            message = self.socket_manager.get_discovery_message()
            if message.direction == "0":
                self.respond_to_discovery_message(message)
                self._log.debug(
                    f'Handled Discovery Message from {message.origin_node.name}')
            elif message.direction == "1":
                directory = message.get_payload()
                self._merge_into_directory(directory)
                self._log.debug(f'Directory updated (n={len(self.directory)})')

    def respond_to_discovery_message(self, message):
        """ Responds to Discovery Message by sending node's directory """
        resp_msg = MessageFactory.generate_discovery_message(
            origin_node=self.socket_manager.node,
            destination_node=message.origin_node,
            direction="1",
            payload=self._serialize_directory())
        self.socket_manager.send_message(resp_msg)
        self.ensure_sender_is_known(message)

    def send_discovery_message(self, destination):
        """ Sends a Discovery Request Message to the destination"""
        discovery_message = MessageFactory.generate_discovery_message(
            origin_node=self.socket_manager.node,
            destination_node=destination,
            direction='0'
        )
        self.socket_manager.send_message(discovery_message)

    def ensure_sender_is_known(self, message):
        """ Send a Discovery message if sender of `message` is unknown """
        if self.directory.get(message.origin_node.get_name(), False):
            self.send_discovery_message(message.origin_node)

    """ 
    Heartbeat Functions

    Send a Heartbeat Message to all other ContactNodes to ensure they are still
    online and functioning. If a node goes offline or a new node comes online
    the RTT task should be kicked off to decide on a new Central Node
    """

    def watch_for_heartbeat_messages(self):
        """ Waits and handles all heartbeat messages that arrive to this node. """
        pass

    def respond_to_heartbeat_message(self):
        """ Respond to a Heartbeat Message """
        pass

    def send_heartbeat_messages(self):
        """ Sends a Heartbeat Message to all ContactNodes """
        pass

    """ 
    Round Trip Time (RTT) Functions

    Handles calculating the RTT to all ContactNodes and broadcasting the sum to
    all ContactNodes in the directory. The ContactNode with the shortest RTT
    will be used to broadcast application messages.
    """

    def watch_for_rtt_messages(self):
        """ Waits and handles all RTT messages that arrive to this node. """
        pass

    def respond_to_rtt_message(self):
        """ Respond to a RTT Message """
        pass

    def send_rtt_messages(self):
        """ Sends a RTT Message to all ContactNodes """
        pass

    """ 
    Util Functions
    """

    def _start_daemon_thread(self, fn):
        """ Allows any function to be started in a Daemon Thread """
        daemon = Thread(target=fn, daemon=True)
        daemon.start()

    def _serialize_directory(self):
        """ Serializes the ContactNode Directory to JSON """
        directory = []
        for key in self.directory:
            directory.append(self.directory[key].to_json())
        return json.dumps(directory)

    def _merge_into_directory(self, serialized_directory):
        """ Adds an array of serialized ContactNodes to the Directory """
        for item in serialized_directory:
            node = ContactNode.create_from_json(item)
            self.directory[node.name] = node
