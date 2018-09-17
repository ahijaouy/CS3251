#!/usr/bin/env python3
"""
Project 1
"""

import argparse
import socket
from abc import ABCMeta, abstractmethod


class SocketClient(metaclass=ABCMeta):

    def __init__(self, **kwargs):
        self.HOST = kwargs.get('host', '127.0.0.1')
        self.PORT = kwargs.get('port', 3000)

    def generate_16_byte_string(self, data):
        to_fill = 16 - len(data)

        if data[0] != "+" and data[0] != "-":
            sign = "+" if float(data) >= 0 else ""
            data = sign + data
            to_fill -= 1

        if data.find(".") == -1:
            to_fill -= 1
            return data + "." + ("0" * to_fill)
        else:
            return data + ("0" * to_fill)

    def generate_packet_string(self, user_input):
        result = user_input.split()
        return self.generate_16_byte_string(result[0]) + self.generate_16_byte_string(result[2]) + result[1]

    def parse_server_response(self, resp):
        result = resp[0:16]
        short_message = resp[16:]
        if short_message[0:4] == "ERR:":
            return short_message
        else:
            return "Result: %s\n%s" % (result, short_message)

    def should_disconnect(self, prompt):
        user_command = str(prompt).lower()
        return user_command.find('quit') != -1

    @abstractmethod
    def connect(self):
        pass


class TCPSocketClient(SocketClient):
    def connect(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.HOST, self.PORT))

            while True:
                prompt = input(
                    "Provide a math problem to solve (format: num1 operand num2)")
                if self.should_disconnect(prompt):
                    print("Closing socket connection.")
                    sock.close()
                    break
                prompt = self.generate_packet_string(prompt)

                print("About to send: ", prompt.encode())

                sock.sendall(prompt.encode())

                data = sock.recv(1024).decode()
                print(self.parse_server_response(data))


class UDPSocketClient(SocketClient):
    def connect(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            server_address = (self.HOST, self.PORT)
            while True:
                prompt = input(
                    "Provide a math problem to solve (format: num1 operand num2)")
                if self.should_disconnect(prompt):
                    print("Closing socket connection.")
                    sock.close()
                    break
                prompt = self.generate_packet_string(prompt)

                print("About to send: ", prompt.encode())

                sock.sendto(prompt.encode(), server_address)

                data, address = sock.recvfrom(1024)
                print(self.parse_server_response(data.decode()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Remote Calculator Client')
    parser.add_argument("protocol", help="Select TCP or UDP")
    parser.add_argument("server", help="Provide Server IP to use")
    parser.add_argument("port", help="Provide Server Port to use")
    args = parser.parse_args()

    client_socket = None
    if args.protocol == "UDP":
        client_socket = UDPSocketClient(host=args.server, port=int(args.port))
    elif args.protocol == "TCP":
        client_socket = TCPSocketClient(host=args.server, port=int(args.port))
    else:
        print("The protoclol '%s' you provided is invalid." % args.protocol)
        raise ValueError
    client_socket.connect()
