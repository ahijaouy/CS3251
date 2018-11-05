from star_node import StarNode
import socket
import time
from threading import Thread

node_1 = StarNode(name="Node1", port=3000, num_nodes=3, verbose=True)

node_1.start_non_blocking()

host = socket.gethostbyname(socket.gethostname())
# host = "127.0.0.1"
node_2 = StarNode(name="Node2", port=3001, num_nodes=3,
                  poc_ip=host, poc_port=3000, verbose=True)

node_2.start_non_blocking()

time.sleep(6)
print("~~~~~~~~~~~About to Add new node")
node_3 = StarNode(name="Node3", port=3002, num_nodes=3,
                  poc_ip=host, poc_port=3000, verbose=True)
node_3.start_non_blocking()


# time.sleep(6)
# print("~~~~~~~~~~~About to send string message")
# node_1.broadcast_string("TESTING 123! TESTING 123")

time.sleep(5)
print("~~~~~~~~~~~About to send file message")

with open('test.txt', 'r') as f:
    file_data = f.read()
    print("TRYING TO SEND:")
    print(file_data)
    node_1.broadcast_file("test.txt", file_data)


# # time.sleep(5)
# print("check directories")
# print("Node1: ", len(node_1.directory))
# for node in node_1.directory:
#     print(node)
# print("Node2: ", len(node_2.directory))
# for node in node_2.directory:
#     print(node)

# def listen(sock):

#     try:
#         while True:
#             print(">>>>>Socket is listening!!!")
#             data, address = sock.recvfrom(1024)
#             print("Packet has been received!", data)

#     except Exception as e:
#         print(
#             f'Exception {e} occured in Socket Manager while listening for packets:', e)


# sock1_address = (socket.gethostname(), 3000)
# sock2_address = (socket.gethostname(), 3001)

# # with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock2:
# sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# sock2.bind(sock2_address)
# # test_message = "Testing123"

# listen_thread_2 = Thread(target=listen, kwargs={"sock": sock2})
# listen_thread_2.start()
# print("Socket 2 listening!")

# time.sleep(2)
# print("About to send message")
# sock.sendto(test_message.encode(), sock2_address)
# print("Message sent!")

# with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock1:

# sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# sock1.bind(sock1_address)
# test_message = "Testing123"

# listen_thread = Thread(target=listen, kwargs={"sock": sock1})
# listen_thread.start()

# time.sleep(2)
# print("About to send message")
# sock1.sendto(test_message.encode(), sock2_address)
# print("Message sent!")


# class Test():
#     num = 0

#     @classmethod
#     def inc(cls):
#         cls.num += 1
#         print(cls.num)

# Test.inc()
# Test.inc()
# Test.inc()
