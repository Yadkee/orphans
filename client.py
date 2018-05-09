#! python3
from socket import socket as newSocket
from secure import (fromDer, generate_password,
                    encrypt, decrypt, PASS_SIZE)
from threading import Thread

from logging import (basicConfig, getLogger, DEBUG)
basicConfig(format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = getLogger("Client")
logger.setLevel(DEBUG)


class Client():
    def __init__(self, name):
        self.name = name.encode()
        # Read serverAdress file
        with open("serverAddress", "rb") as f:
            args = f.read().split(b"\n\r")
        name, ip = (i.decode() for i in args[:2])
        port = int.from_bytes(args[2], "big")
        serverCipher = fromDer(args[3])
        self.server = (name, ip, port, serverCipher)
        logger.info("Read serverAdress")

    def send(self, raw):
        data = encrypt(raw, self.password)
        self.s.sendall(len(data).to_bytes(1, "big") + data)

    def run(self):
        def read(metasize):
            size = int.from_bytes(s.recv(metasize), "big")
            data = decrypt(s.recv(size), password)
            return data

        def send(data):
            s.sendall(len(data).to_bytes(1, "big") + data)
        serverCipher = self.server[3]
        password = generate_password(PASS_SIZE)
        self.password = password
        firstMsg = serverCipher.encrypt(password + self.name)
        logger.info("Connecting to the server")
        s = newSocket()
        self.s = s
        try:
            s.connect(self.server[1:3])
        except ConnectionRefusedError:
            logger.error("Connection refused by the server")
            return
        # Send password
        s.sendall(firstMsg)
        # Receive confirmation
        logger.info(read(1))  # Should be b"RECEIVED"
        # Receive lobby info and queue
        logger.info(read(3))
        logger.info(read(3))
        # Start loop
        while True:
            data = read(1)
            if data == b".":
                send(encrypt(b",", password))
                logger.debug("Answered the ping")
            else:
                logger.info(data)


if __name__ == "__main__":
    client = Client("Peter")
    Thread(target=client.run, daemon=True).start()
    while True:
        inp = input()
        enc = []
        replace = 0
        for i in inp:
            if i == "#":
                replace = 4
                number = None
            elif replace:
                if replace & 1:
                    enc.append(int(number + i, 16))
                else:
                    number = i
                replace -= 1
            else:
                enc.append(ord(i))
        client.send(bytes(enc))
