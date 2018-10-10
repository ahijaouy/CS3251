#!/usr/bin/env python3
"""
Socket Manager

Provides an interface for Star Node to manage the socket.
Messages can be queued up to be sent.
Also provides functions that block and return messages when they arrive
Ex: SocketManager.get_rtt_message() will block until an RTT message is recieved
"""

import queue
from threading import Thread
from message_factory import MessageFactory
from reliable_socket import ReliableSocket
from logger import Logger


class SocketManager():
    def __init__(self, name, port, host, report_func, verbose=False):
        self.report = report_func
        self.log = Logger(name, verbose)
        self.outbox = queue.Queue()
        self.sock = ReliableSocket(
            port, self._process_incoming_packet, self.outbox, host, name, verbose)

        self.messages = {
            "heartbeat": queue.Queue(),
            "rtt": queue.Queue(),
            "discovery": queue.Queue(),
            "app": queue.Queue(),
            "ack": queue.Queue(),
        }

    def get_address(self):
        return self.sock.get_address()

    def start(self):
        listening_thread = Thread(
            target=self.sock.start_listening, daemon=True)
        listening_thread.start()
        self.log.debug("Socket Listening Thread started")
        sending_thread = Thread(target=self.sock.start_sending, daemon=True)
        sending_thread.start()
        self.log.debug("Socket Sending Thread started")

    def send_message(self, message):
        self.outbox.put(message)
        self.log.debug(
            f'Message added to outbox. Outbox size: {self.outbox.qsize()} ')

    def _process_incoming_packet(self, data, address):
        """
        Takes an incomming packet and uses the Type field of the packet
        to put it in the proper message queue.
        """
        # self.log.debug("Processing new message")
        new_message = MessageFactory.create_message(
            packet_data=data,
            origin=address,
            destination=self.get_address())
        self._put_new_message_in_queue(new_message)
        self.report()

    def _put_new_message_in_queue(self, message):
        """
        Takes paresed data from incomming messaged and uses the Type field 
        of the packet to put it in the proper message queue.
        """
        message_type = message.TYPE_STRING
        self.messages[message_type].put(message)
        self.log.debug(f'New Message of type: {message_type}')

    def get_heartbeat_message(self):
        return self.messages["heartbeat"].get()

    def get_rtt_message(self):
        return self.messages["rtt"].get()

    def get_discovery_message(self):
        return self.messages["discovery"].get()

    def return_discovery_message(self, message):
        return self.messages["discovery"].put(message)

    def get_app_message(self):
        return self.messages["app"].get()

    def get_ack_message(self):
        return self.messages["ack"].get()
