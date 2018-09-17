#!/usr/bin/env python3

"""
Project 1

"""

import argparse
import socket
from abc import ABCMeta, abstractmethod


class SocketServer(metaclass=ABCMeta):

    def __init__(self, **kwargs):
        # self.HOST = kwargs.get('host', '127.0.0.1')
        self.HOST = socket.gethostname()
        # self.HOST = "127.0.0.1"
        self.PORT = kwargs.get('port', 3000)
        print("Socket created!\nHost:%s\nPort:%s" %
              (self.HOST, str(self.PORT)))

    def generate_16_byte_string(self, data):
        if(len(data) > 16):
            return data[:16]

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

    def generate_packet_string(self, result, error=None):
        if error == None:
            byte_string = self.generate_16_byte_string(result)
            return byte_string + "Generated by Andre Hijaouy's Server."
        else:
            return ("0" * 16) + error

    def parse_client_response(self, resp):
        num1 = resp[0:16]
        num2 = resp[16:32]
        operand = resp[32:33]
        return (num1, num2, operand)

    def _is_valid_float(self, data):
        try:
            float1 = float(data)
            return True, float1
        except ValueError:
            print("ERR: Number '%s' not valid" % data)
            return False, "ERR: Number '%s' not valid" % data

    def _is_valid_operand(self, data):
        if "+-*/".find(data) == -1:
            print("ERR: Operand '%s' not valid" % data)
            return False, "ERR: Operand '%s' not valid" % data
        return True, data

    def _is_valid(self, num1, num2, operand):
        float1_valid, float1 = self._is_valid_float(num1)
        float2_valid, float2 = self._is_valid_float(num2)
        operand_valid, operand1 = self._is_valid_operand(operand)

        if operand == "/" and float2_valid and float2 == 0.0:
            print("ERR: Cannot divide by 0.0")
            return False, "ERR: Cannot divide by 0.0"

        if float1_valid and float2_valid and operand_valid:
            return True, (float1, float2, operand)
        elif float1_valid == False:
            return False, float1
        elif float2_valid == False:
            return False, float2
        elif operand_valid == False:
            return False, operand1

    def do_calculation(self, float1, float2, operand):
        result = None
        if operand == "+":
            result = float1 + float2
        elif operand == "-":
            result = float1 - float2
        elif operand == "*":
            result = float1 * float2
        elif operand == "/":
            result = float1 / float2
        return str(result)

    def handle_client_connection(self, data):
        (num1, num2, operand) = self.parse_client_response(data)
        (is_valid, details) = self._is_valid(num1, num2, operand)
        if is_valid:
            (float1, float2, operand) = details
            result = self.do_calculation(float1, float2, operand)
            return self.generate_packet_string(result)
        return self.generate_packet_string(result=None, error=details)

    @abstractmethod
    def connect(self):
        pass


class TCPSocketServer(SocketServer):
    def connect(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((self.HOST, self.PORT))
            sock.listen()

            try:
                while True:
                    # accept connections from outside
                    (clientsocket, address) = sock.accept()
                    # now do something with the clientsocket
                    # in this case, we'll pretend this is a threaded server
                    with clientsocket:
                        print("Connected to client: ", address)
                        while True:

                            data = clientsocket.recv(1024)
                            if not data:
                                print("Disconnected from client:", address)
                                break
                            data = data.decode()
                            print("Received from client", data)

                            result = self.handle_client_connection(data)

                            clientsocket.sendall(result.encode())
            except KeyboardInterrupt:
                print("Closing server socket")
            finally:
                sock.close()


class UDPSocketServer(SocketServer):
    def connect(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind((self.HOST, self.PORT))

            try:
                while True:
                    data, address = sock.recvfrom(1024)
                    print("Contacted by client: ", address)
                    print("Received from client", data)
                    result = self.handle_client_connection(data.decode())

                    sock.sendto(result.encode(), address)
            except KeyboardInterrupt:
                print("Closing server socket")
            finally:
                sock.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Remote Calculator Server')
    parser.add_argument("protocol", help="Select TCP or UDP")
    parser.add_argument("port", help="Select Port to use")
    args = parser.parse_args()

    server_socket = None
    if args.protocol == "UDP":
        server_socket = UDPSocketServer(port=int(args.port))
    elif args.protocol == "TCP":
        server_socket = TCPSocketServer(port=int(args.port))
    else:
        print("The protoclol '%s' you provided is invalid." % args.protocol)
        raise ValueError

    server_socket.connect()
