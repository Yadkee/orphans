#! python3
from socket import socket as newSocket
from secure import (fromDer, generate_password,
                    encrypt, decrypt, PASS_SIZE)

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

    def run(self):
        def read(metasize):
            size = int.from_bytes(s.recv(metasize), "big")
            data = decrypt(s.recv(size), password)
            return data

        def send(data):
            s.sendall(len(data).to_bytes(1, "big") + data)
        serverCipher = self.server[3]
        password = generate_password(PASS_SIZE)
        firstMsg = serverCipher.encrypt(password + self.name)
        logger.info("Connecting to the server")
        s = newSocket()
        try:
            s.connect(self.server[1:3])
        except ConnectionRefusedError:
            logger.error("Connection refused by the server")
            return
        # Send password
        s.sendall(firstMsg)
        # Receive confirmation
        logger.info(read(1))  # Should be b"RECEIVED"
        # Receive lobby info
        logger.info(read(3))
        # Start loop
        while True:
            data = read(1)
            if data == b"PING":
                send(encrypt(b"PONG", password))
            else:
                logger.info(data)


if __name__ == "__main__":
    client = Client("Peter")
    client.run()
