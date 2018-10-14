#!/usr/bin/env python3
"""
Socket Manager

Provides an interface for Star Node to manage the socket.
Messages can be queued up to be sent.
Also provides functions that block and return messages when they arrive
Ex: SocketManager.get_rtt_message() will block until an RTT message is recieved
"""

from queue import Queue
from threading import Thread

from reliable_socket import ReliableSocket
from contact_node import ContactNode
from message_factory import MessageFactory
from logger import Logger


class SocketManager():
    def __init__(self, name, port, host, report_func, verbose=False):
        self._log = Logger(name, verbose)
        self.report = report_func
        self.outbox = Queue()
        self.sock = ReliableSocket(
            port, self._process_incoming_packet, self.outbox, host, name, verbose)

        self.node = ContactNode(name, self.sock.get_ip(), port)
        self.messages = {
            "heartbeat": Queue(),
            "rtt": Queue(),
            "discovery": Queue(),
            "app": Queue(),
            "ack": Queue(),
        }

    def start(self):
        """ Initializes the Socket and begins listening and sending """
        listening_thread = Thread(
            target=self.sock.start_listening, daemon=True)
        listening_thread.start()
        sending_thread = Thread(target=self.sock.start_sending, daemon=True)
        sending_thread.start()
        self._log.debug("Socket Online...")
        self.report()

    def send_message(self, message):
        """ Queues up a message to be sent out """
        self.outbox.put(message)
        self._log.debug(
            f'Message added to outbox. Outbox size: {self.outbox.qsize()} ')

    def _process_incoming_packet(self, data, address):
        """
        Takes an incomming packet and uses the Type field of the packet
        to put it in the proper message queue.
        """
        new_message = MessageFactory.create_message(
            packet_data=data,
            origin_address=address,
            destination_node=self.node)
        self._put_new_message_in_queue(new_message)
        self.report()

    def _put_new_message_in_queue(self, message):
        """
        Takes paresed data from incomming messaged and uses the Type field 
        of the packet to put it in the proper message queue.
        """
        message_type = message.TYPE_STRING
        self.messages[message_type].put(message)
        self._log.debug(f'New Message of type: {message_type}')

    def get_heartbeat_message(self):
        """ Blocks and returns a heartbeat message when avaiable """
        return self.messages["heartbeat"].get()

    def get_rtt_message(self):
        """ Blocks and returns a RTT message when avaiable """
        return self.messages["rtt"].get()

    def get_discovery_message(self):
        """ Blocks and returns a discovery message when avaiable """
        return self.messages["discovery"].get()

    def get_app_message(self):
        """ Blocks and returns an application message when avaiable """
        return self.messages["app"].get()

    def get_ack_message(self):
        """ Blocks and returns an ACK message when avaiable """
        return self.messages["ack"].get()
