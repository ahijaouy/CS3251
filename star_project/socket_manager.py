#!/usr/bin/env python3
"""
Socket Manager

Provides an interface for Star Node to send/recieve messages and implements 
reliable message transmission

Parameters:
    - name: Name of the StarNode this socket is attached to
    - port: Port number to listen on
    - report_func: function to be called whenever a packet is received
    - verbose: Indicates whether output should be printed with the logger
"""

from queue import Queue
from threading import Thread
import time

from reliable_socket import ReliableSocket
from contact_node import ContactNode
from message_factory import MessageFactory
from logger import Logger


class SocketManager():
    ACK_TIMEOUT = 1.5  # seconds

    def __init__(self, name, port, report_func, verbose=False):
        self._log = Logger(name, verbose)
        self.report = report_func
        self.outbox = Queue()
        self.awaiting_ack = Queue()
        self.sock = ReliableSocket(
            port, self.process_incoming_packet, self.outbox, name, verbose=False)

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

        ack_watch_thread = Thread(target=self.watch_for_acks, daemon=True)
        ack_watch_thread.start()

        ack_timeout_thread = Thread(
            target=self.watch_for_ack_timeout, daemon=True)
        ack_timeout_thread.start()

        self.report()

    # def send_message(self, message):
    #     """ Queues up a message to be sent out """
    #     self.outbox.put(message)
    #     self._log.debug(
    #         f'Message {message.TYPE_STRING} added to outbox. Outbox size: {self.outbox.qsize()} ')

    def send_message(self, message):
        """ Queues up a message to be sent out """
        self.outbox.put(message)
        if message.TYPE_STRING != "ack":
            self.awaiting_ack.put((message, time.time()))
        self._log.debug(
            f'Message {message.TYPE_STRING} added to outbox. Outbox size: {self.outbox.qsize()} ')

    def watch_for_acks(self):
        """ Wait for incoming ACKs and start a therad to process them """
        while True:
            ack_message = self.messages['ack'].get()
            self._log.debug("ACK Received")
            process_ack_thread = Thread(
                target=self.process_ack, args=(ack_message,), daemon=True)
            process_ack_thread.start()

    def process_ack(self, ack_message):
        """ Find the message being ACK'd and mark it received by sender """
        processing = True
        while processing:
            sent_message, time_sent = self.awaiting_ack.get()
            if sent_message.get_message_id() == ack_message.ack_id:
                processing = False
                self._log.debug("ACK Processed")
            else:
                self.awaiting_ack.put((sent_message, time_sent))

    def watch_for_ack_timeout(self):
        """ 
        Cycles through all messages in the awaiting ack queue and if
        any message is still in the queue after ACK_TIMEOUT seconds, resend it
        """
        while True:
            sent_message, time_sent = self.awaiting_ack.get()
            timeout_time = time.time() + self.ACK_TIMEOUT
            if time_sent + self.ACK_TIMEOUT < time.time():
                sent_message.resent += 1
                if sent_message.resent < 5:
                    self.send_message(sent_message)
                    self._log.write_to_log(
                        "ACK", f"Resending message {sent_message.uuid} to {sent_message.destination_node.get_name()}")
                else:
                    self._log.write_to_log(
                        "ACK", f"Drop message to {sent_message.destination_node.get_name()}")
            else:
                self.awaiting_ack.put((sent_message, time_sent))

            time.sleep(.3)  # Ensure this thread doesn't hog the queue

    def process_incoming_packet(self, data, address):
        """
        Takes an incomming packet and uses the Type field of the packet
        to put it in the proper message queue. Responds to sender w/ ACK packet
        """
        new_message = MessageFactory.create_message(
            packet_data=data,
            origin_address=address,
            destination_node=self.node)
        self._put_new_message_in_queue(new_message)
        self.report()
        if new_message.TYPE_STRING != "ack":
            ack_message = MessageFactory.generate_ack_message(new_message)
            self._log.debug("Sending ACK")
            self.send_message(ack_message)

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
