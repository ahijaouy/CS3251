#!/usr/bin/env python3
"""
Messages

Contains classes for all different types of messages used in the StarNet.
"""
import json
import random
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

        name = packet_string[1:17]
        origin_node = ContactNode(name, origin_address[0], origin_address[1])
        uuid = packet_string[17:21]
        payload_kwargs = cls.parse_payload_to_kwargs(packet_string[21:])
        return cls(
            uuid=packet_string[17:21],
            origin_node=origin_node,
            destination_node=destination_node,
            **payload_kwargs
        )

    def to_packet_string(self):
        """ Convert Message object to string to be sent in packet"""
        packet_string = self.TYPE_CODE + \
            self.get_message_id() + self.serialize_payload_for_packet()
        return packet_string
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

    @classmethod
    def parse_payload_to_kwargs(cls, packet_payload):
        """ Parse package payload string to a dict to be passed to constructor """
        return {
            'direction': packet_payload[0],
            'payload': packet_payload[1:]
        }

    def serialize_payload_for_packet(self):
        """ Specify how to serialize Message Payload to packet string """
        return self.direction + self.payload


class HeartbeatMessage(BaseMessage):
    TYPE_STRING = "heartbeat"
    TYPE_CODE = "H"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.direction = kwargs.get("direction", '0')

    @classmethod
    def parse_payload_to_kwargs(cls, packet_payload):
        """ Parse package payload string to a dict to be passed to constructor """
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
    Stage 3: Broadcast current shortest RTT
    """
    TYPE_STRING = "rtt"
    TYPE_CODE = "R"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stage = kwargs.get("stage", '0')
        self.rtt_sum = kwargs.get("rtt_sum", "")
        self.central_node = kwargs.get("central_node", "")
        if self.central_node != "":
            self.central_node = format(self.central_node, '>16')

    @classmethod
    def parse_payload_to_kwargs(cls, packet_payload):
        """ Parse package payload string to a dict to be passed to constructor """
        stage = packet_payload[0]
        if stage == "3":
            return {
                'stage': packet_payload[0],
                'central_node': packet_payload[1:17],
                'rtt_sum': packet_payload[17:]
            }
        return {
            'stage': packet_payload[0],
            'rtt_sum': packet_payload[1:]
        }

    def serialize_payload_for_packet(self):
        """ Specify how to serialize Message Payload to packet string """
        return self.stage + self.central_node + str(self.rtt_sum)

    def get_rtt_sum(self):
        if self.stage == '2' or self.stage == '3':
            return float(self.rtt_sum)

    def get_central_node(self):
        if self.stage == "3":
            return self.central_node.strip()


class AppMessage(BaseMessage):
    TYPE_STRING = "app"
    TYPE_CODE = "A"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.forward = kwargs.get('forward', '0')
        self.is_file = kwargs.get('is_file', '0')
        self.data = kwargs.get('data')

    @classmethod
    def parse_payload_to_kwargs(cls, packet_payload):
        """ Parse package payload string to a dict to be passed to constructor """
        return {
            'forward': packet_payload[0],
            'is_file': packet_payload[1],
            'data': packet_payload[2:]
        }

    def serialize_payload_for_packet(self):
        """ Specify how to serialize Message Payload to packet string """
        return self.forward + self.is_file + self.data


class AckMessage(BaseMessage):
    TYPE_STRING = "ack"
    TYPE_CODE = "K"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ack_id = kwargs.get('ack_id')

    @classmethod
    def parse_payload_to_kwargs(cls, packet_payload):
        """ Parse package payload string to a dict to be passed to constructor """
        return {"ack_id": packet_payload}

    def serialize_payload_for_packet(self):
        """ Specify how to serialize Message Payload to packet string """
        return self.ack_id
