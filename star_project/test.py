from star_node import StarNode
import socket
import time
from threading import Thread

node_1 = StarNode(name="Node1", port=3000, num_nodes=2, verbose=True)

node_1.start_non_blocking()

host = socket.gethostbyname(socket.gethostname())
# host = "127.0.0.1"
node_2 = StarNode(name="Node2", port=3001, num_nodes=2, poc_name="Node1",
                  poc_ip=host, poc_port=3000, verbose=True)

node_2.start_non_blocking()


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
