#!/usr/bin/env python3
"""
Socket Manager
"""

import socket
import time
import threading
import queue
from message_factory import MessageFactory


class SocketManager():
    def __init__(self, args, **kwargs):
        # self.HOST = kwargs.get('host', '127.0.0.1')
        self.LISTENING = False
        self.HOST = socket.gethostname()
        self.PORT = int(kwargs.get("port", 3000))
        self.NAME = kwargs.get("name", "Default Name")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.HOST, self.PORT)
        self.heartbeat_messages = queue.Queue()
        self.rtt_messages = queue.Queue()
        self.discovery_messages = queue.Queue()
        self.app_messages = queue.Queue()
        self.ack_messages = queue.Queue()
        self.messages = {
            "heartbeat": queue.Queue(),
            "rtt": queue.Queue(),
            "discovery": queue.Queue(),
            "app": queue.Queue(),
            "ack": queue.Queue(),
        }

    def send(self, data, destination):
        self.sock.sendto(data.encode(), destination)

    def stop_listening(self):
        self.LISTENING = False

    def start_listening(self):
        self.LISTENING = True
        try:
            while self.LISTENING:
                data, address = self.sock.recvfrom(1024)
                self._process_incoming_packet(data, address)

        except Exception as e:
            print(f'Exception {e} occured in Socket Manager: {self.NAME}', e)
        finally:
            self.sock.close()

    def _process_incoming_packet(self, data, address):
        """
        Takes an incomming packet and uses the Type field of the packet
        to put it in the proper message queue.
        """
        new_message = MessageFactory.create_message(data, address)
        self._put_new_message_in_queue(new_message)

    def _put_new_message_in_queue(self, message):
        """
        Takes paresed data from incomming messaged and uses the Type field 
        of the packet to put it in the proper message queue.
        """
        self.messages[message["type"]].put(message)

    def get_heartbeat_message(self):
        return self.messages["heartbeat"].get()

    def mark_heartbeat_message_read(self):
        if self.messages["heartbeat"].not_empty:
            self.messages["heartbeat"].task_done()

    def get_rtt_message(self):
        return self.messages["rtt"].get()

    def mark_rtt_message_read(self):
        if self.messages["rtt"].not_empty:
            self.messages["rtt"].task_done()

    def get_discovery_message(self):
        return self.messages["discovery"].get()

    def mark_discovery_message_read(self):
        if self.messages["discovery"].not_empty:
            self.messages["discovery"].task_done()

    def get_app_message(self):
        return self.messages["app"].get()

    def mark_app_message_read(self):
        if self.messages["app"].not_empty:
            self.messages["app"].task_done()

    def get_ack_message(self):
        return self.messages["ack"].get()

    def mark_ack_message_read(self):
        if self.messages["ack"].not_empty:
            self.messages["ack"].task_done()
