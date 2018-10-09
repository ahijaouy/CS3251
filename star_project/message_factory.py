#!/usr/bin/env python3
"""
Message Factory
"""


class MessageFactory():

    code_mapping = {
        # TODO Add Mapping
        # EX: "000": DiscoveryMessage,

    }

    @staticmethod
    def _get_message_type(raw_packet_data):
        # TODO Implement Proper length... currently taking first 3
        code_bits = raw_packet_data[:3]
        return self.code_mapping[code_bits]

    @staticmethod
    def create_message(raw_packet_data, address):
        message_type = self._get_message_type(raw_packet_data)
        return message_type(raw_packet_data, address)


class AbstractMessage():
    def __init__(self, raw_packet_data, address):
        self.origin_address = address
        # TODO Add more General Message info


class DiscoveryMessage():
    def __init__(self, raw_packet_data, address):
        TYPE_STRING = "Discovery"
        TYPE_CODE = "000"  # TODO add proper code

        super().__init__(raw_packet_data, address)

        # TODO Add Message specific implementation


class HeartbeatMessage():
    def __init__(self, raw_packet_data, address):
        super().__init__(raw_packet_data, address)
        # TODO Add Message specific implementation


class RTTMessage():
    def __init__(self, raw_packet_data, address):
        super().__init__(raw_packet_data, address)
        # TODO Add Message specific implementation


class AppMessage():
    def __init__(self, raw_packet_data, address):
        super().__init__(raw_packet_data, address)
        # TODO Add Message specific implementation


class AckMessage():
    def __init__(self, raw_packet_data, address):
        super().__init__(raw_packet_data, address)
        # TODO Add Message specific implementation
