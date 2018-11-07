#!/usr/bin/env python3
"""
DiscoveryModule

"""
from threading import Thread
from message_factory import MessageFactory


class DiscoveryModule():

    def __init__(self, socket_manager, directory, logger, calculate_rtt):
        self.socket_manager = socket_manager
        self.directory = directory
        self._log = logger
        self.calculate_rtt = calculate_rtt

    def start_non_blocking(self):
        self._start_thread(self.watch_for_discovery_messages, daemon=True)

    def _start_thread(self, fn, daemon=False):
        """ Allows any function to be started in a Daemon Thread """
        daemon = Thread(target=fn, daemon=daemon)
        daemon.start()

    def watch_for_discovery_messages(self):
        """ Waits and handles all discovery messages that arrive to this node. """
        while True:
            message = self.socket_manager.get_discovery_message()
            if message.disconnect == "1":
                # handle disconnecting node
                self.directory.remove(message.origin_node.get_name())
                # TODO: Should recalculate central node
                self._log.write_to_log(
                    "Discovery", f'{message.origin_node.get_name()} has terminated.')
                self._log.debug(
                    f'Removed {message.origin_node.get_name()} from directory')
            elif message.direction == "0":
                self.respond_to_discovery_message(message)
                self._log.debug(
                    f'Handled Discovery Message from {message.origin_node.name}')
            elif message.direction == "1":
                serialized_directory = message.get_payload()
                self.directory.merge_serialized_directory(serialized_directory)

                self._start_thread(self.calculate_rtt, daemon=True)
                self._log.debug(
                    f'Directory updated (n={self.directory.size()})')

    def respond_to_discovery_message(self, message):
        """ Responds to Discovery Message by sending node's directory """
        resp_msg = MessageFactory.generate_discovery_message(
            origin_node=self.socket_manager.node,
            destination_node=message.origin_node,
            direction="1",
            payload=self.directory.serialize())
        self.socket_manager.send_message(resp_msg)
        self.send_current_central_node(message)
        self.ensure_sender_is_known(message)

    def send_discovery_message(self, destination):
        """ Sends a Discovery Request Message to the destination"""
        self._log.debug(
            f'###### about to send Discovery message to {destination.get_name()}')
        discovery_message = MessageFactory.generate_discovery_message(
            origin_node=self.socket_manager.node,
            destination_node=destination,
            direction='0'
        )
        self.socket_manager.send_message(discovery_message)

    def ensure_sender_is_known(self, message):
        """ Send a Discovery message if sender of `message` is unknown """
        if not self.directory.exists(message.origin_node.get_name()):
            self.send_discovery_message(message.origin_node)

    def send_current_central_node(self, message):
        if self.directory.get_central_node() != None:
            rtt_message = MessageFactory.generate_rtt_message(
                origin_node=self.socket_manager.node,
                destination_node=message.origin_node,
                stage="3",
                rtt_sum=self.shortest_rtt,
                central_node=self.directory.get_central_node()
            )
            self.socket_manager.send_message(rtt_message)
