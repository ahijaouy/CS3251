import socket

host = socket.gethostbyname(socket.gethostname())
port = 3001
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.bind((host, port))
    while True:
        data, address = sock.recvfrom(64000)
        with open("test_image.png", 'wb') as f:
            f.write(data)
