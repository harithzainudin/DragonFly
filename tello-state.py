#!/usr/bin/python

import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', 8890))

while True:
    try:
        data, server = sock.recvfrom(1024)
        print(data.decode())
    except Exception as err:
        print(err)
        sock.close()
        break
