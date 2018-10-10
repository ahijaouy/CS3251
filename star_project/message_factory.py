#!/usr/bin/env python3
"""
Message Factory
"""
import json
from abc import ABCMeta, abstractmethod


class AbstractMessage(metaclass=ABCMeta):
    def __init__(self, uuid, origin, destination, **kwargs):
        self.id = uuid
        self.origin_address = origin
        self.destination_address = destination

    def prepare_packet(self):
        string = self.get_packet_string()
        print("Inside Prepare_Packet: ", string)
        return (self.get_packet_string(), self.destination_address)

    @abstractmethod
    def create_from_packet(cls):
        pass

    @abstractmethod
    def get_packet_string(self):
        pass


class DiscoveryMessage(AbstractMessage):
    TYPE_STRING = "discovery"
    TYPE_CODE = "D"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.direction = kwargs.get('direction', '0')
        self.payload = kwargs.get('payload', '')  # json string

    @classmethod
    def create_from_packet(cls, packet_data, **kwargs):
        return cls(
            direction=packet_data[1],
            payload=packet_data[2:],
            **kwargs)

    @classmethod
    def create_response(cls, uuid, origin, destination, directory):
        return cls(uuid, origin, destination, json.dumps(directory))

    def get_packet_string(self):
        return self.TYPE_CODE + self.direction + self.payload

    def is_response_to(self, original_message):
        if self.direction == "1" and self.origin_address == original_message.destination_address:
            return True
        return False


class HeartbeatMessage(AbstractMessage):
    TYPE_STRING = "heartbeat"
    TYPE_CODE = "H"

    def __init__(self, uuid, address):
        super().__init__(uuid, origin, destination)
        # TODO Add Message specific implementation

    @classmethod
    def create_from_packet(cls, uuid, origin, destination, packet_data):
        pass  # TODO: Implement

    def get_packet_string(self):
        pass  # TODO: Implement


class RTTMessage(AbstractMessage):
    TYPE_STRING = "rtt"
    TYPE_CODE = "R"

    def __init__(self, uuid, address):
        super().__init__(uuid, origin, destination)

        # TODO Add Message specific implementation

    @classmethod
    def create_from_packet(cls, uuid, origin, destination, packet_data):
        pass  # TODO: Implement

    def get_packet_string(self):
        pass  # TODO: Implement


class AppMessage(AbstractMessage):
    TYPE_STRING = "app"
    TYPE_CODE = "A"

    def __init__(self, uuid, address):
        super().__init__(uuid, origin, destination)

        # TODO Add Message specific implementation

    @classmethod
    def create_from_packet(cls, uuid, origin, destination, packet_data):
        pass  # TODO: Implement

    def get_packet_string(self):
        pass  # TODO: Implement


class AckMessage(AbstractMessage):
    TYPE_STRING = "ack"
    TYPE_CODE = "K"

    def __init__(self, uuid, address):
        super().__init__(uuid, origin, destination, sent_id)
        self.sent_id = sent_id

        # TODO Add Message specific implementation

    @classmethod
    def create_from_packet(cls, uuid, origin, destination, packet_data):
        sent_id = packet_data[1:2]
        return cls(uuid, origin, destination, sent_id)

    def get_packet_string(self):
        return self.TYPE_CODE + self.sent_id


class MessageFactory():

    uuid = 0
    code_mapping = {
        "D": DiscoveryMessage,
        "H": HeartbeatMessage,
        "R": RTTMessage,
        "A": AppMessage,
        "K": AckMessage
    }

    @classmethod
    def get_new_id(cls):
        new_id = cls.uuid
        cls.uuid += 1
        return new_id

    @classmethod
    def _get_message_type(cls, raw_packet_data):
        code_bit = raw_packet_data[:1]
        return cls.code_mapping[code_bit]

    @classmethod
    def create_message(cls, packet_data, **kwargs):
        message_type = cls._get_message_type(packet_data)
        return message_type.create_from_packet(packet_data, uuid=cls.get_new_id(), **kwargs)

    @classmethod
    def generate_ack_message(cls, packet_data, address):
        ack = AckMessage.create_from_packet(
            cls.get_new_id(), address, packet_data)
        return ack

    @classmethod
    def generate_discovery_message(cls, **kwargs):
        return DiscoveryMessage(uuid=cls.get_new_id(), **kwargs)
