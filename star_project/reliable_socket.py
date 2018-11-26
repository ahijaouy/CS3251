#!/usr/bin/env python3
"""
Simple Socket -- Custom API to send and receive UDP Packets.


Parameters:
    - port: Port number to listen on
    - process_incoming_packet_func: function to be called whenever a packet is received
    - outbox: Queue that contains messages to be sent out
    - name: Name of the StarNode this socket is attached to
    - verbose: Indicates whether output should be printed with the logger
"""

import socket
from logger import Logger


class ReliableSocket():

    def __init__(self, port, process_incoming_packet_func, outbox, name, verbose=False):
        # Verify Parameters are correct
        self._verify_int(port)
        self._verify_func(process_incoming_packet_func)

        # Setup Instance Variables
        self.process_incoming_packet = process_incoming_packet_func
        self._log = Logger(name, verbose)
        self.outbox = outbox

        # Setup Socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.host = socket.gethostbyname(socket.gethostname())
        self.sock.bind((self.host, port))

    def start_listening(self):
        """ Blocks and listens for incoming packets """
        try:
            while True:
                data, address = self.sock.recvfrom(655070)
                # self.send_ack(data, address)
                self.process_incoming_packet(data, address)

        except Exception as e:
            print(e)
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
            self.sock.sendto(data, destination)
            if message.TYPE_CODE == "A":
                print("APP MESSAGE SENT SUCCESSFULLY")
            return message.uuid
        except Exception as e:
            print(e)
            self._log.error("in ReliableSocket while sending message", e)

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
