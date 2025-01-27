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
import queue
import os
from threading import Thread
from contact_directory import ContactDirectory
from contact_node import ContactNode
from socket_manager import SocketManager
from message_factory import MessageFactory
from logger import Logger


class StarNode():
    # Timeout constants
    RTT_TIMEOUT = 5  # seconds
    NO_CONTACT_TIMEOUT = 60 * 3  # 3 minutes
    INITIAL_RTT_DEFAULT = 10
    RTT_COUNTDOWN_INIT = 15

    def __init__(self, name, port, num_nodes, poc_ip=0, poc_port=0, verbose=False):
        # Initialize instance variables
        self._log = Logger(name, verbose=verbose)
        self._log.clear_log()
        self.num_nodes = num_nodes
        self.central_node = None  # Stores name of central node
        self.shortest_rtt = self.INITIAL_RTT_DEFAULT  # placeholder
        self.rtt_calcd_for_size = 0

        self.rtt_queue = queue.Queue()
        self.rtt_countdown = time.time() + self.RTT_COUNTDOWN_INIT
        self.directory = ContactDirectory(name, verbose)
        if poc_ip != 0 and poc_port != 0:
            self.poc = ContactNode("poc", poc_ip, poc_port)
        else:
            self.poc = None

        # Initialize things related to the socket
        self.socket_manager = SocketManager(
            name, port, self.report, verbose)
        self.directory.set_star_node(self.socket_manager.node)
        self.name = self.socket_manager.node.get_name()

    """
    General Control Functions
    """

    def start(self):
        """ Startes the StarNode and kicks off all lifecycle functions"""
        self.socket_manager.start()

        if self.poc != None:
            self._start_thread(self.contact_poc, daemon=True)
            self.send_discovery_message(self.poc)
        self._start_thread(self.watch_for_discovery_messages, daemon=True)
        self._start_thread(self.watch_for_heartbeat_messages, daemon=True)
        self._start_thread(self.send_heartbeat_messages, daemon=True)
        self._start_thread(self.watch_for_heartbeat_timeouts, daemon=True)
        self._start_thread(self.watch_for_rtt_messages, daemon=True)
        self._start_thread(self.calculate_rtt_timer, daemon=True)
        self._start_thread(self.watch_for_app_messages, daemon=True)

        while True:  # Blocking. Nothing can go below this
            self.check_for_inactivity()

    def start_non_blocking(self):
        """ Allows StarNode to be started without blocking """
        self._start_thread(self.start, daemon=True)

    def print_log(self):
        self._log.print_log()

    def disconnect(self):
        for node in self.directory.get_current_list():
            bye_message = MessageFactory.generate_discovery_message(
                origin_node=self.socket_manager.node,
                destination_node=node,
                disconnect="1"
            )
            self.socket_manager.send_message(bye_message)
        self._log.write_to_log("Terminated", 'Node has gracefully terminated.')

        import sys
        sys.exit(f'{self.name} has gracefully terminated.')

    def report(self):
        """ Updates the time a packet was last received from {message.get_sender()} """
        self.last_contacted = time.time()

    def check_for_inactivity(self):
        """
        Monitors when the node was last active.

        If node has been inactive (received no packets) for more than
        3 minutes (NO_CONTACT_TIMEOUT) then terminated program
        """
        if self.last_contacted + self.NO_CONTACT_TIMEOUT < time.time():
            import sys
            sys.exit("StarNode terminated due to inactivity with other nodes")

    """
    Application Message Functions

    """

    def watch_for_app_messages(self):
        while True:
            message = self.socket_manager.get_app_message()
            if message.forward == "1":
                self.broadcast_as_central_node(message)
                self._log.write_to_log(
                    "Message", f'Message from {message.origin_node.get_name()} forwarded as central node.')
            if message.is_file == "1":
                self.handle_app_message_file(message)
            else:
                self.handle_app_message(message)

    def handle_app_message(self, message):
        """
        Handles displaying the app message to the user
        """
        to_print = f'\nMessage recieved from: {message.get_sender()}...\n'
        to_print += message.data
        to_print += '\nStar-node command:'
        print(to_print)
        self._log.write_to_log(
            "Message", f'Message received from {message.get_sender()} ')

    def handle_app_message_file(self, message):
        with open(f'{self.name}-{message.file_name}', 'wb') as f:
            f.write(message.data)
        to_print = f'\nMessage recieved from: {message.get_sender()}...\n'
        to_print += f'File recieved: {message.file_name}\n'
        to_print += 'Star-node command:'
        print(to_print)
        self._log.write_to_log(
            "Message", f'Message received from {message.get_sender()} ')

    def broadcast_string(self, data):
        """
        Sends a string message to all nodes in the network via the Central Node
        """
        app_message = MessageFactory.generate_app_message(
            origin_node=self.socket_manager.node,
            destination_node=self.directory.get(self.central_node),
            forward='1',
            is_file='0',
            sender=self.socket_manager.node.get_16_byte_name(),
            data=data,
        )

        if self._is_central_node():
            self.broadcast_as_central_node(app_message)
        else:
            self.socket_manager.send_message(app_message)
        self._log.write_to_log("Message", f'Message sent to all nodes.')

    def broadcast_file(self, file_name, data):
        app_message = MessageFactory.generate_app_message(
            origin_node=self.socket_manager.node,
            destination_node=self.directory.get(self.central_node),
            forward='1',
            is_file='1',
            sender=self.socket_manager.node.get_16_byte_name(),
            file_name=file_name,
            data=data,
        )

        if self._is_central_node():
            self.broadcast_as_central_node(app_message)
        else:
            self.socket_manager.send_message(app_message)
        self._log.write_to_log("Message", f'Message sent to all nodes.')

    def broadcast_as_central_node(self, message):
        for node in self.directory.get_current_list():
            if node.get_name() != message.origin_node.get_name():
                app_message = MessageFactory.generate_app_message(
                    origin_node=self.socket_manager.node,
                    destination_node=node,
                    forward='0',
                    is_file=message.is_file,
                    file_name=message.file_name,
                    sender=message.sender,
                    data=message.data,
                )
                self.socket_manager.send_message(app_message)

    def _is_central_node(self):
        return self.central_node == self.name

    """
    Peer Discovery Functions

    Handle contacting POC Node, responding to new Discovery Requests, and
    ensuring all incoming requests are from known ContactNodes.
    """

    def contact_poc(self):
        while self.directory.poc_not_added(self.poc):
            self.send_discovery_message(self.poc)
            time.sleep(2)

    def watch_for_discovery_messages(self):
        """ Waits and handles all discovery messages that arrive to this node. """
        while True:
            message = self.socket_manager.get_discovery_message()
            if message.disconnect == "1":
                self.handle_disconnect(message)
            elif message.direction == "0":
                self.respond_to_discovery_message(message)
            elif message.direction == "1":
                serialized_directory = message.get_payload()
                self.directory.merge_serialized_directory(serialized_directory)
                self.initiate_rtt_calculation()

    def handle_disconnect(self, message):
        name = message.origin_node.get_name()
        self.directory.remove(name)
        self.initiate_rtt_calculation()
        self._log.write_to_log("Discovery", f'{name} has terminated.')

    def respond_to_discovery_message(self, message):
        """ Responds to Discovery Message by sending node's directory """
        resp_msg = MessageFactory.generate_discovery_message(
            origin_node=self.socket_manager.node,
            destination_node=message.origin_node,
            direction="1",
            payload=self.directory.serialize())
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
        if not self.directory.exists(message.origin_node.get_name()):
            self.shortest_rtt = 8
            self.send_discovery_message(message.origin_node)
            self._log.write_to_log(
                "Discovery", "Message received from unknown sender.")

    """
    Heartbeat Functions

    Send a Heartbeat Message to all other ContactNodes to ensure they are still
    online and functioning. If a node goes offline or a new node comes online
    the RTT task should be kicked off to decide on a new Central Node
    """

    def watch_for_heartbeat_timeouts(self):
        while True:
            for node in self.directory.get_current_list():
                if node.is_unresponsive():
                    self.directory.remove(node.name)
                    self.initiate_rtt_calculation()
                    self._log.write_to_log(
                        "Heartbeat", f'{node.name} has stopped responding.')
            time.sleep(2)

    def watch_for_heartbeat_messages(self):
        """ Waits and handles all heartbeat messages that arrive to this node. """
        while True:
            message = self.socket_manager.get_heartbeat_message()
            self.ensure_sender_is_known(message)
            if message.direction == "0":
                self.respond_to_heartbeat_message(message)
            elif message.direction == "1":
                self.handle_heartbeat_response(message)

    def handle_heartbeat_response(self, message):
        """ Handle a response Heartbeat message """
        self.directory.get(message.origin_node.get_name()).heartbeat()

    def respond_to_heartbeat_message(self, message):
        """ Respond to a Heartbeat Message """
        heartbeat_message = MessageFactory.generate_heartbeat_message(
            origin_node=self.socket_manager.node,
            destination_node=message.origin_node,
            direction="1"
        )
        self.socket_manager.send_message(heartbeat_message)

    def send_heartbeat_messages(self):
        """ Sends a Heartbeat Message to all ContactNodes """
        while True:
            for node in self.directory.get_current_list():
                heartbeat_message = MessageFactory.generate_heartbeat_message(
                    origin_node=self.socket_manager.node,
                    destination_node=node
                )
                self.socket_manager.send_message(heartbeat_message)
            time.sleep(3)

    """
    Round Trip Time (RTT) Functions

    Handles calculating the RTT to all ContactNodes and broadcasting the sum to
    all ContactNodes in the directory. The ContactNode with the shortest RTT
    will be used to broadcast application messages.
    """

    def watch_for_rtt_messages(self):
        """ Waits and handles all RTT messages that arrive to this node. """
        while True:
            message = self.socket_manager.get_rtt_message()
            self.ensure_sender_is_known(message)
            if message.stage == "0":
                self.respond_to_rtt_message(message)
            elif message.stage == "1":
                self.handle_rtt_response(message)
            elif message.stage == "2":
                self.handle_rtt_broadcast(message)

    def respond_to_rtt_message(self, message):
        """ Respond to a RTT Message """
        rtt_message = MessageFactory.generate_rtt_message(
            origin_node=self.socket_manager.node,
            destination_node=message.origin_node,
            stage="1"
        )
        self.socket_manager.send_message(rtt_message)
        self._log.write_to_log(
            "RTT", f'Response sent to {message.origin_node.get_name()} ')

    def handle_rtt_response(self, message):
        sender = message.origin_node.get_name()
        self._log.write_to_log(
            "RTT", f'Response received from {sender}. RTT to node is {message.get_rtt()} ')
        self.rtt_queue.put((sender, message))

    def handle_rtt_broadcast(self, message):
        new_rtt_sum = message.get_rtt_sum()
        sender = message.origin_node.get_name()
        network_size = message.get_network_size()
        self.directory.get(sender).update_rtt_sum(new_rtt_sum, network_size)

        self._log.write_to_log(
            "RTT", f'Received RTT Sum Broadcast from {sender}. RTT Sum: {new_rtt_sum} ')

        self.set_central_node()

    def initiate_rtt_calculation(self, when=3):
        self.rtt_countdown = time.time() + when
        if self.directory.size() != self.rtt_calcd_for_size:
            self.shortest_rtt = 9

    def calculate_rtt_timer(self):
        """
        Blocks and calculates RTT whenever self.rtt_countdown < time.time()
        """
        try:
            while True:
                while time.time() < self.rtt_countdown:
                    time.sleep(.5)
                prev_time = self.rtt_countdown
                self.calculate_rtt()
                if self.rtt_countdown == prev_time:
                    self.rtt_countdown = time.time() + self.RTT_COUNTDOWN_INIT
        except Exception as e:
            print(e)

    def calculate_rtt(self):
        """ Sends a RTT Message to all ContactNodes """
        self._log.write_to_log("RTT", "Starting new RTT Calc")
        node_list = self.directory.get_current_list()
        for node in node_list:
            rtt_message = MessageFactory.generate_rtt_message(
                origin_node=self.socket_manager.node,
                destination_node=node
            )
            self.socket_manager.send_message(rtt_message)
            self._log.write_to_log("RTT", f'Request sent to {node.get_name()}')

        timeout = time.time() + 6
        rtt_responses = {}
        while (time.time() < timeout) and (len(rtt_responses) < len(node_list)):
            try:
                name, message = self.rtt_queue.get(timeout=2)
                rtt_responses[name] = message.get_rtt()
            except Exception as e:
                pass

        if len(rtt_responses) == len(node_list):
            self.process_rtt_times(rtt_responses)
        else:
            self.initiate_rtt_calculation(when=1)
            self._log.write_to_log(
                "RTT", "Timed out waiting for RTT Responses.")

    def process_rtt_times(self, rtt_responses):
        # Calculate RTT Times
        rtt_sum = 0.0
        for name, rtt in rtt_responses.items():
            rtt_sum += rtt
            self.directory.get(name).rtt = rtt
        self._log.write_to_log("RTT", f'New RTT sum computed: {rtt_sum} ')
        self.directory.star_node.update_rtt_sum(rtt_sum, self.directory.size())

        self.set_central_node()

        # Broadcast RTT Sums
        for node in self.directory.get_current_list():
            rtt_message = MessageFactory.generate_rtt_message(
                origin_node=self.socket_manager.node,
                destination_node=node,
                stage="2",
                network_size=self.directory.size(),
                rtt_sum=rtt_sum
            )
            self.socket_manager.send_message(rtt_message)

    def set_central_node(self):
        name, rtt = self.directory.check_central_node()
        self.central_node = name
        self.shortest_rtt = rtt
        self._log.write_to_log("RTT", f'Central Node: {name}')

    """
    Util Functions
    """

    def _start_thread(self, fn, daemon=False):
        """ Allows any function to be started in a Daemon Thread """
        daemon = Thread(target=fn, daemon=daemon)
        daemon.start()


if __name__ == "__main__":
    print(f'Current Host: {socket.gethostbyname(socket.gethostname())}')

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'name', help='an ASCII string (Min: 1 character, Max: 16 characters) that names that star-node', type=str)
    parser.add_argument(
        'local_port', help='the UDP port number that this star-node should use (for peer discovery)', type=int)
    parser.add_argument(
        'poc_address', help='the host-name of the PoC for this star-node. Set to 0 if this star-node does not have a PoC', type=str)
    parser.add_argument(
        'poc_port', help='the UDP port number of the PoC for this star-node. Set to 0 if this star-node does not have a PoC', type=int)
    parser.add_argument('n', help='the maximum number of star-nodes', type=int)
    args = parser.parse_args()

    star = StarNode(name=args.name, port=args.local_port, num_nodes=args.n,
                    poc_ip=args.poc_address, poc_port=args.poc_port, verbose=False)
    star.start_non_blocking()

    running = True
    while running:
        command_in = input('Star-node command: ')
        command = command_in.split()

        if command[0] == 'send':
            if os.path.isfile(command[1]):
                file_name = command[1]
                with open(file_name, 'rb') as f:
                    file_data = f.read()
                    star.broadcast_file(file_name, file_data)
            else:
                string_to_send = ' '.join(command[1:])
                star.broadcast_string(string_to_send)

        elif command[0] == 'show-status':
            d = []
            rtt_sum = 0
            print("\n--------- Current Status ---------")
            print(format("Name", "<16"), "RTT")
            for node in star.directory.get_current_list():
                print(format(node.get_name(), "<16"), node.rtt)
                rtt_sum += node.rtt
            print(f'\nMy RTT sum: {rtt_sum}\n')
            print(f'\nCentral Node: {star.central_node}')
            print(f'Shortest RTT: {star.shortest_rtt}\n')

        elif command[0] == 'disconnect':
            star.disconnect()
            running = False

        elif command[0] == 'show-log':
            star.print_log()

        else:
            help_message = "Please enter a valid StarNode command.\n"
            help_message += "Command: send <message or file>\n"
            help_message += "Command: show-status\n"
            help_message += "Command: show-log\n"
            help_message += "Command: disconnect\n"
            print(help_message)
