#!/usr/bin/env python3
"""
Message Factory

Provides functionality to create all the different types of messages a StarNet
node can send.
"""

from messages import DiscoveryMessage, HeartbeatMessage, RTTMessage, AppMessage, AckMessage


class MessageFactory():
    LENGTH_OF_ID = 4
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
        new_id = str(cls.uuid % (10 ** cls.LENGTH_OF_ID))
        new_id = new_id.zfill(cls.LENGTH_OF_ID)
        cls.uuid += 1
        return new_id

    @classmethod
    def _get_message_type(cls, raw_packet_data):
        code_bit = raw_packet_data[:1]
        return cls.code_mapping[code_bit]

    @classmethod
    def create_message(cls, packet_data, **kwargs):
        message_type = cls._get_message_type(packet_data)
        return message_type.from_packet_string(
            packet_string=packet_data, **kwargs)

    @classmethod
    def generate_ack_message(cls, message):
        return AckMessage(
            uuid=cls.get_new_id(),
            origin_node=message.destination_node,
            destination_node=message.origin_node,
            ack_id=message.get_message_id()
        )

    @classmethod
    def generate_discovery_message(cls, **kwargs):
        return DiscoveryMessage(uuid=cls.get_new_id(), **kwargs)

    @classmethod
    def generate_heartbeat_message(cls, **kwargs):
        return HeartbeatMessage(uuid=cls.get_new_id(), **kwargs)

    @classmethod
    def generate_rtt_message(cls, **kwargs):
        return RTTMessage(uuid=cls.get_new_id(), **kwargs)

    @classmethod
    def generate_app_message(cls, **kwargs):
        return AppMessage(uuid=cls.get_new_id(), **kwargs)
