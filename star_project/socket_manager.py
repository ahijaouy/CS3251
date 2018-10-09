#!/usr/bin/env python3
"""
Socket Manager
"""

import socket
import time
import threading
import queue


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

    def stop_listening(self):
        self.LISTENING = False

    def start_listening(self):
        self.LISTENING = True
        try:
            while self.LISTENING:
                data, address = self.sock.recvfrom(1024)
                self.process_incoming_packet(data, address)

        except Exception as e:
            print(f'Exception {e} occured in Socket Manager: {self.NAME}', e)
        finally:
            self.sock.close()

    def process_incoming_packet(self, data, address):
        """
        Takes an incomming packet and uses the Type field of the packet
        to put it in the proper message queue.
        """
        packet_type = data["type"]

    def put_new_message_in_queue(self, message, address):
        """
        Takes paresed data from incomming messaged and uses the Type field 
        of the packet to put it in the proper message queue.
        """
        packet_type = message["type"]
        self.messages[packet_type].put(message)

    def send(self, data, destination):
        self.sock.sendto(data.encode(), destination)

    def get_heartbeat_message(self):
        return self.heartbeat_messages.get()

    def mark_heartbeat_message_read(self):
        if self.heartbeat_messages.not_empty:
            self.heartbeat_messages.task_done()

    def get_rtt_message(self):
        return self.rtt_messages.get()

    def mark_rtt_message_read(self):
        if self.rtt_messages.not_empty:
            self.rtt_messages.task_done()

    def get_discovery_message(self):
        return self.discovery_messages.get()

    def mark_discovery_message_read(self):
        if self.discovery_messages.not_empty:
            self.discovery_messages.task_done()

    def get_app_message(self):
        return self.app_messages.get()

    def mark_app_message_read(self):
        if self.app_messages.not_empty:
            self.app_messages.task_done()

    def get_ack_message(self):
        return self.ack_messages.get()

    def mark_ack_message_read(self):
        if self.ack_messages.not_empty:
            self.ack_messages.task_done()
