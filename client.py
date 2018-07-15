#! python3
from socket import socket as newSocket
from secure import (fromDer, generate_password,
                    encrypt, decrypt, PASS_SIZE)

from logging import (basicConfig, getLogger, DEBUG)
basicConfig(format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = getLogger("Client")
logger.setLevel(DEBUG)


class Client():
    def __init__(self):
        self.name = ""
        # Read serverAdress file
        with open("serverAddress", "rb") as f:
            args = f.read().split(b"\n\r")
        name, ip = (i.decode() for i in args[:2])
        port = int.from_bytes(args[2], "big")
        serverCipher = fromDer(args[3])
        self.server = (name, ip, port, serverCipher)
        logger.info("Read serverAdress")

    def esend(self, raw):
        data = encrypt(raw, self.password)
        self.s.sendall(len(data).to_bytes(1, "big") + data)

    def admin(self, data):
        try:
            with open("secret", "rb") as f:
                secret = f.read()
        except FileNotFoundError:
            return
        else:
            self.esend(b"/" + secret)
            self.esend(data)

    def process_text(self, text):
        if text.startswith("/"):
            client.admin(text[1:].encode())
            return
        enc = []
        replace = 0
        for i in text:
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
        client.esend(bytes(enc))

    def run(self):
        def read(metasize):
            size = int.from_bytes(s.recv(metasize), "big")
            data = decrypt(s.recv(size), password)
            return data
        # Generate password and encrypt it
        password = generate_password(PASS_SIZE)
        self.password = password
        firstMsg = self.server[3].encrypt(password + self.name)
        # Create the socket
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

        self.tags = set()
        self.users = dict()
        self.queue = set()
        self.queueFlags = dict()
        # Locals
        esend = self.esend
        tags = self.tags
        users = self.users
        queue = self.queue
        queueFlags = self.queueFlags
        try:
            callback = self.callback
        except AttributeError:
            callback = print

        while True:
            data = read(1)
            if data == b".":
                esend(b",")
                logger.debug("Answered the ping")
            elif data == b"INFO":
                # Receive lobby info and queue
                tags.clear()
                queue.clear()
                queueFlags.clear()
                rUsers = read(3).split(b";")
                if rUsers != [b""]:
                    for user in rUsers:
                        tag = user[:2]
                        tags.add(tag)
                        users[tag] = user[2:]
                rQueue = read(3).split(b";")
                if rQueue != [b""]:
                    for i in rQueue:
                        queue.add(i[:2])
                        queueFlags[i[:2]] = i[2:]
                callback("LOBBY")
            elif data.startswith(b"!"):
                callback("PLAY", data[1:])
            elif data == b"START":
                callback("START")
            elif data.startswith(b":"):
                callback("MOVE", data[1:])
            elif data.startswith(b"="):
                callback("JOIN", data[1:])
            elif data.startswith(b"+"):
                tag = data[1:3]
                tags.add(tag)
                users[tag] = data[3:]
                callback("U")
            elif data.startswith(b"-"):
                tag = data[1:]
                del users[tag]
                tags.remove(tag)
                queue.discard(tag)
                queueFlags.pop(tag, None)
                callback("U")
            elif data.startswith(b"?"):
                user = data[1:3]
                flags = data[3:]
                if flags:
                    queue.add(user)
                    queueFlags[user] = flags
                else:
                    queue.remove(user)
                callback("U")
            else:
                logger.warn(data)


if __name__ == "__main__":
    from threading import Thread
    client = Client()
    client.name = b"Peter"
    Thread(target=client.run, daemon=True).start()
    while True:
        client.process_text(input())
