#!/usr/bin/env python3
"""
Socket Manager
"""

import socket
import time
import queue
from messages import AckMessage
from message_factory import MessageFactory
from logger import Logger


class ReliableSocket():
    ACK_TIMEOUT = 5  # seconds

    def __init__(self, port, process_incoming_packet_func, outbox, host=None, name="Reliable Socket", verbose=False):
        # Verify Parameters are correct
        self._verify_int(port)
        self._verify_func(process_incoming_packet_func)

        # Setup Instance Variables
        self.process_incoming_packet = process_incoming_packet_func
        self._log = Logger(name, verbose)
        self.outbox = outbox
        self.acks = queue.Queue()

        # Setup Socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = socket.gethostbyname(socket.gethostname())
        self.sock.bind((self.host, port))

    def start_listening(self):
        """ Blocks and listens for incoming packets """
        try:
            self._log.debug(f'Socket is listening...')
            while True:

                data, address = self.sock.recvfrom(1024)
                self._log.debug(f'Socket received packet from: {address[0]}')
                # self.send_ack(data, address)
                self.process_incoming_packet(data.decode(), address)

        except Exception as e:
            self._log.error("in ReliableSocket while listening for packets", e)
        finally:
            self.sock.close()

    def start_sending(self):
        """ Blocks and sends messages that are queued up in the outbox """
        try:
            self._log.debug(f'Socket is ready to send...')
            while True:
                message_to_send = self.outbox.get()
                self.send(message_to_send)
                self._log.debug(
                    f'Packet sent successfully. Outbox size: {self.outbox.qsize()}')

        except Exception as e:
            self._log.error("in ReliableSocket while sending message", e)

    def get_ip(self):
        """ Returns the IP of the socket """
        return self.host

    def send(self, message):
        """ Send a Message as a UDP Packet """
        data, destination = message.prepare_packet()
        try:
            self.sock.sendto(data.encode(), destination)
            self._log.debug(
                f'Message of type {message.TYPE_STRING} sent to {destination[0]}')
            return message.uuid
        except Exception as e:
            self._log.error("in ReliableSocket while sending message", e)

    def send_ack(self, ack_id):
        # TODO
        pass
        # ack = AckMessage

    def send_reliably(self, message):
        # TODO: Should retry if ack is not recieved
        sent_id = self.send(message)
        timeout_time = time.time() + self.ACK_TIMEOUT

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

    """ 
    Util Functions
    """

    def _verify_int(self, var_to_test):
        """ Verify the var_to_test is an integer """
        if type(var_to_test) != int:
            raise ValueError(
                f'Expected an integer. Recieved type: {type(var_to_test)}')

    def _verify_func(self, var_to_test):
        """ Verify the var_to_test is a function """
        if not callable(var_to_test):
            raise ValueError(
                f'Expected a function. Recieved type: {type(var_to_test)}')
