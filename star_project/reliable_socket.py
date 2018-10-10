#!/usr/bin/env python3
"""
Socket Manager
"""

import socket
import time
import queue
from message_factory import MessageFactory, AckMessage
from logger import Logger


class ReliableSocket():
    def __init__(self, port, process_incoming_packet_func, outbox, host=None, name="Reliable Socket", verbose=False):
        self._verify_int(port)
        self._verify_func(process_incoming_packet_func)
        self.log = Logger(name, verbose)

        self.outbox = outbox

        # self.host = host if host else socket.gethostname()
        # self.host = "127.0.0.1"
        self.host = socket.gethostname()
        self.port = port
        self.is_listening = False
        self.ack_timeout = 5  # seconds
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.process_incoming_packet = process_incoming_packet_func
        self.sock.bind((self.host, self.port))
        self.acks = queue.Queue()

    def _verify_int(self, port):
        if type(port) != int:
            raise ValueError(
                f'Expected an integer. Recieved type: {type(port)}')

    def _verify_func(self, func):
        if not callable(func):
            raise ValueError(
                f'Expected a function. Recieved type: {type(func)}')

    def send(self, message):
        data, destination = message.prepare_packet()

        try:
            self.sock.sendto(data.encode(), destination)
            self.log.debug(
                f'Message of type {message.TYPE_STRING} sent to {destination[0]}')
            return message.id
        except Exception as e:
            self.log.error("in ReliableSocket while sending message", e)

    def send_ack(self, ack_id):
        pass
        # ack = AckMessage

    def send_reliably(self, message):
        # TODO: Should retry if ack is not recieved
        sent_id = self.send(message)
        timeout_time = time.time() + self.ack_timeout

        while timeout_time > time.time():
            try:
                ack = self.acks.get(
                    timeout=timeout_time - time.time())
                if ack.sent_id == sent_id:
                    return True
                else:
                    self.acks.put(ack)
            except Exception as e:
                pass
        return False

    def start_listening(self):
        try:
            self.log.debug(f'Socket is listening...')
            while True:

                data, address = self.sock.recvfrom(1024)
                self.log.debug(f'Socket received packet from: {address[0]}')
                # self.send_ack(data, address)
                # self.process_incoming_packet(data, address)

        except Exception as e:
            self.log.error("in ReliableSocket while listening for packets", e)
        finally:
            self.sock.close()

    def start_sending(self):
        try:
            self.log.debug(f'Socket is ready to send...')
            while True:
                message_to_send = self.outbox.get()
                self.send(message_to_send)
                self.log.debug(
                    f'Packet sent successfully. Outbox size: {self.outbox.qsize()}')

        except Exception as e:
            self.log.error("in ReliableSocket while sending message", e)
