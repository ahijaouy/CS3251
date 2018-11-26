#!/usr/bin/env python3
"""
Messages

Contains classes for all different types of messages used in the StarNet.
"""
import json
import random
import time
from contact_node import ContactNode


class BaseMessage():
    """
    Holds all the information regarding a packet

    Properties:
    - uuid: unique identifier for this message. Format = sender_name + packet_num
    - origin_node: ContactNode object representing origin of packet
    - destination_node: ContactNode object representing destination of packet
    - payload: JSON string representing packet payload. Use self.get_payload()
    to get the corrosponding python dict

    Inheritance:
    - Implement classmethod parse_payload_to_kwargs to specify how the packet
    payload should be parsed and stored in the message object
    - Overide self.serialize_payload_for_packet() to specify how self.payload
    should be serialized before sending
    """
    TYPE_STRING = None
    TYPE_CODE = None

    def __init__(self, uuid, origin_node, destination_node, payload='{}', **kwargs):
        self.uuid = uuid
        self.origin_node = self._ensure_contact_node(origin_node)
        self.destination_node = self._ensure_contact_node(destination_node)
        self.payload = self._ensure_json_string(payload)
        self.resent = 0

    """
    Functions to Override
    """
    @classmethod
    def parse_payload_to_kwargs(cls, packet_payload):
        """ Parse package payload string to a dict to be passed to constructor """
        return {}

    def serialize_payload_for_packet(self):
        """ Specify how to serialize Message Payload to packet string """
        return self.payload

    """
    General Functions
    """

    def prepare_packet(self):
        """ Return Tuple with string to send in packet & address tuple """
        return (self.to_packet_string(), self.destination_node.get_address())

    def get_payload(self):
        """ Returns message payload as dictionary or None if no payload """
        if self.payload != None:
            return json.loads(self.payload)
        return None

    def get_message_id(self):
        """ Get the combination of the origin name and uuid """
        return self.origin_node.get_16_byte_name() + self.uuid

    @classmethod
    def from_packet_string(cls, origin_address, destination_node, packet_string):
        """ Create a Message Instance from information received in a packet """

        name = packet_string[1:17].decode()
        origin_node = ContactNode(name, origin_address[0], origin_address[1])
        uuid = packet_string[17:21].decode()
        payload_kwargs = cls.parse_payload_to_kwargs(packet_string[21:])
        return cls(
            uuid=packet_string[17:21].decode(),
            origin_node=origin_node,
            destination_node=destination_node,
            **payload_kwargs
        )

    def to_packet_string(self):
        """ Convert Message object to string to be sent in packet"""
        # packet_string = self.TYPE_CODE + \
        #     self.get_message_id() + self.serialize_payload_for_packet()

        packet_string = self.TYPE_CODE + self.get_message_id()
        packet_string = packet_string.encode()

        serialized_payload = self.serialize_payload_for_packet()
        if type(serialized_payload) != bytes:
            serialized_payload = serialized_payload.encode()
        return packet_string + serialized_payload
    """
    Util Functions
    """

    def _ensure_json_string(self, json_string):
        """ Ensure json_string is valid JSON """
        if not isinstance(json_string, str):
            raise TypeError(f'Expected String, received: {type(json_string)}')
        try:
            json_object = json.loads(json_string)
            return json_string
        except ValueError as e:
            raise ValueError(f'Expected valid JSON. Recieved:\n {json_string}')

    def _ensure_contact_node(self, node):
        """ Ensure node is instance of ContactNode """
        if isinstance(node, ContactNode):
            return node
        raise TypeError(f'Expected a Contact Node. Received {type(node)}')


class DiscoveryMessage(BaseMessage):
    TYPE_STRING = "discovery"
    TYPE_CODE = "D"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.direction = kwargs.get('direction', '0')
        self.disconnect = kwargs.get('disconnect', '0')

    @classmethod
    def parse_payload_to_kwargs(cls, packet_payload):
        """ Parse package payload string to a dict to be passed to constructor """
        packet_payload = packet_payload.decode()
        return {
            'direction': packet_payload[0],
            'disconnect': packet_payload[1],
            'payload': packet_payload[2:]
        }

    def serialize_payload_for_packet(self):
        """ Specify how to serialize Message Payload to packet string """
        return self.direction + self.disconnect + self.payload


class HeartbeatMessage(BaseMessage):
    TYPE_STRING = "heartbeat"
    TYPE_CODE = "H"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.direction = kwargs.get("direction", '0')

    @classmethod
    def parse_payload_to_kwargs(cls, packet_payload):
        """ Parse package payload string to a dict to be passed to constructor """
        packet_payload = packet_payload.decode()
        return {
            'direction': packet_payload[0],
        }

    def serialize_payload_for_packet(self):
        """ Specify how to serialize Message Payload to packet string """
        return self.direction


class RTTMessage(BaseMessage):
    """
    Stage 0: RTT Initial Request
    Stage 1: RTT Response
    Stage 2: Broadcast RTT Time
    """
    TYPE_STRING = "rtt"
    TYPE_CODE = "R"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stage = kwargs.get("stage", '0')
        self.rtt_sum = kwargs.get("rtt_sum", "")
        self.send_time = kwargs.get("send_time", "")
        self.rtt_id = kwargs.get("rtt_id", "")
        self.network_size = kwargs.get("network_size", "")
        self.init_time = time.time()

    @classmethod
    def parse_payload_to_kwargs(cls, packet_payload):
        """ Parse package payload string to a dict to be passed to constructor """
        packet_payload = packet_payload.decode()
        stage = packet_payload[0]
        if stage == "2":
            return {
                'stage': packet_payload[0],
                'network_size': packet_payload[1],
                'rtt_sum': packet_payload[2:]
            }
        return {
            'stage': packet_payload[0],
            # 'rtt_id': packet_payload[1],
            'send_time': packet_payload[1:]
        }

    def serialize_payload_for_packet(self):
        """ Specify how to serialize Message Payload to packet string """
        if self.stage == "2":
            return self.stage + str(self.network_size) + str(self.rtt_sum)
        # Add send time
        return self.stage + str(self.rtt_id) + str(time.time())

    def get_rtt_sum(self):
        if self.stage == '2':
            return float(self.rtt_sum)

    def get_rtt(self):
        if self.stage != '2':
            return self.init_time - float(self.send_time)

    def get_network_size(self):
        if self.stage == "2":
            return int(self.network_size)


class AppMessage(BaseMessage):
    TYPE_STRING = "app"
    TYPE_CODE = "A"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.forward = kwargs.get('forward', '0')
        self.is_file = kwargs.get('is_file', '0')
        self.file_name = kwargs.get('file_name', '')
        self.sender = kwargs.get('sender')
        self.data = kwargs.get('data')

    def get_sender(self):
        return self.sender.strip()

    def file_name_length(self):
        return format(len(self.file_name), '>2')

    @classmethod
    def parse_payload_to_file_kwargs(cls, packet_payload):
        file_name_length = int(packet_payload[18:20].decode())
        file_name = packet_payload[20: 20 + file_name_length].decode()
        data = packet_payload[20 + file_name_length:]

        return {
            'forward': packet_payload[0:1].decode(),
            'is_file': packet_payload[1:2].decode(),
            'sender':  packet_payload[2:18].decode(),
            'file_name': file_name,
            'data': data
        }

    @classmethod
    def parse_payload_to_kwargs(cls, packet_payload):
        """ Parse package payload string to a dict to be passed to constructor """

        if packet_payload[1:2].decode() == '1':
            return cls.parse_payload_to_file_kwargs(packet_payload)

        # parse payload to string kwargs
        packet_payload = packet_payload.decode()
        return {
            'forward': packet_payload[0],
            'is_file': packet_payload[1],
            'sender':  packet_payload[2:18],
            'data': packet_payload[18:]
        }

    def serialize_payload_for_file_packet(self):
        non_file_part = self.forward + self.is_file + self.sender + self.file_name_length() \
            + self.file_name
        return non_file_part.encode() + self.data

    def serialize_payload_for_packet(self):
        """ Specify how to serialize Message Payload to packet string """

        if self.is_file == '1':
            return self.serialize_payload_for_file_packet()

        return self.forward + self.is_file + self.sender + self.data


class AckMessage(BaseMessage):
    TYPE_STRING = "ack"
    TYPE_CODE = "K"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ack_id = kwargs.get('ack_id')

    @classmethod
    def parse_payload_to_kwargs(cls, packet_payload):
        """ Parse package payload string to a dict to be passed to constructor """
        packet_payload = packet_payload.decode()
        return {"ack_id": packet_payload}

    def serialize_payload_for_packet(self):
        """ Specify how to serialize Message Payload to packet string """
        return self.ack_id
