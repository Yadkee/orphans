#! python3
from socket import socket as newSocket
from secure import (rsa, generate_password, encrypt, decrypt, PASS_SIZE)
from threading import Thread
from time import (time, sleep)

from logging import (basicConfig, getLogger, DEBUG)
basicConfig(format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = getLogger("Server")
logger.setLevel(DEBUG)

NICKNAME_MAX_SIZE = 16
MAX_USERS = 256
PING_RATE = 30
AFK_RATE = 600


def send(socket, data):
    socket.sendall(len(data).to_bytes(1, "big") + data)


class Server():
    def __init__(self, name, ip, port):
        self.address = (ip, port)
        self.publicKey, self.privateCipher = rsa()
        # Create serverAddress file
        encoded = (name.encode(), ip.encode(), port.to_bytes(2, "big"),
                   self.publicKey)
        with open("serverAddress", "wb") as f:
            f.write(b"\n\r".join(encoded))
        logger.info("Created serverAddress")

    def join_lobby(self, address):
        def user(a):
            return ids[a] + names[a].encode()
        sockets, passwords, names, ids, lobby, times = self.locals

        users = b";".join(map(user, lobby))
        message = encrypt(users, passwords[address])
        sockets[address].sendall(len(message).to_bytes(3, "big") + message)
        logger.debug("[Lobby] +%s" % str(user(address)))
        self.notify_lobby(b"+" + user(address))
        lobby.append(address)
        times[address] = time()

    def notify_lobby(self, data):
        sockets, lobby, passwords = self.sockets, self.lobby, self.passwords
        for address in lobby:
            send(sockets[address], encrypt(data, passwords[address]))

    def left(self, address):
        sockets, passwords, names, ids, lobby, times = self.locals
        logger.info("-%s [%d]" % (address, len(lobby)))
        self.notify_lobby(b"-" + ids[address] + names[address].encode())
        try:
            sockets[address].close()
        except (ConnectionResetError, ConnectionAbortedError):
            pass
        del (sockets[address], passwords[address],
             names[address], ids[address], times[address])

    def run(self):
        def handle(socket, address):
            message = socket.recv(256)
            decrypted = sdecrypt(message)
            password, rawName = decrypted[:PASS_SIZE], decrypted[PASS_SIZE:]
            name = "".join(chr(i) for i in rawName)[:NICKNAME_MAX_SIZE]
            logger.debug("Received %s's (%s) password" % (name, address))
            send(socket, encrypt(b"RECEIVED", password))

            socket.setblocking(False)
            sockets[address] = socket
            passwords[address] = password
            names[address] = name
            myId = generate_password(2)
            while myId in ids.values():
                myId = generate_password(2)
            ids[address] = myId
            join_lobby(address)
        s = newSocket()
        s.bind(self.address)
        s.listen(5)

        self.pinged = set()
        self.locals = ({}, {}, {}, {}, [], {})
        sockets, passwords, names, ids, lobby, _ = self.locals
        (self.sockets, self.passwords, self.names,
         self.ids, self.lobby, self.times) = self.locals
        sdecrypt = self.privateCipher.decrypt
        join_lobby = self.join_lobby
        Thread(target=self.lobby_loop, daemon=True).start()
        Thread(target=self.ping_loop, daemon=True).start()

        while True:
            socket, raw = s.accept()
            address = raw[0] + ":" + str(raw[1])
            if len(lobby) >= MAX_USERS:
                socket.close()
                logger.info("?%s size limit exceeded" % address)
                continue
            logger.info("+%s [%d]" % (address, len(lobby) + 1))
            Thread(target=handle, args=(socket, address), daemon=True).start()

    def ping_loop(self):
        lobby, pinged, times = self.lobby, self.pinged, self.times
        notify_lobby = self.notify_lobby
        while True:
            t0 = time()
            for address in pinged:
                if address in self.sockets:
                    lobby.remove(address)
                    self.left(address)
            pinged.clear()
            notify_lobby(b"PING")
            logger.debug("PINGED")
            for address, timestamp in times.items():
                if timestamp + AFK_RATE < t0:
                    lobby.remove(address)
                    self.left(address)
            pinged.update(lobby)
            sleep(PING_RATE - time() + t0)

    def lobby_loop(self):
        sockets, passwords, lobby, pinged = (self.sockets, self.passwords,
                                             self.lobby, self.pinged)
        while True:
            for address in lobby:
                try:
                    size = int.from_bytes(sockets[address].recv(1), "big")
                    if not size:
                        raise ConnectionAbortedError
                except BlockingIOError:
                    continue
                except (ConnectionResetError, ConnectionAbortedError):
                    lobby.remove(address)
                    Thread(target=self.left,
                           args=(address,), daemon=True).start()
                else:
                    data = decrypt(sockets[address].recv(size),
                                   passwords[address])
                    if data == b"PONG":
                        pinged.discard(address)
                    else:
                        logger.info("%s: %s" % (address, str(data)))


if __name__ == "__main__":
    logger.info("Start")
    server = Server("TestServer", "localhost", 0xCE55)
    server.run()
