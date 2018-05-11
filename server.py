#! python3
from socket import socket as newSocket
from secure import (rsa, encrypt, decrypt, PASS_SIZE)
from threading import Thread
from time import (time, sleep)
from collections import deque
from itertools import chain

from logging import (basicConfig, getLogger, DEBUG)
basicConfig(format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = getLogger("Server")
logger.setLevel(DEBUG)

NICKNAME_MAX_SIZE = 16
MAX_USERS = 256
PING_RATE = 30
AFK_RATE = 600


def send(socket, data, size=1):
    socket.sendall(len(data).to_bytes(size, "big") + data)


def esend(socket, raw, password, size=1):
    try:
        data = encrypt(raw, password)
        socket.sendall(len(data).to_bytes(size, "big") + data)
    except (ConnectionResetError, ConnectionAbortedError):
        pass


def userToStr(user):
    return user[2:].decode() + "#" + user[:2].hex()


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
        # Locals
        lobby = self.lobby
        users = self.users
        queue = self.queue
        queueFlags = self.queueFlags

        user = users.pop(address)
        userList = b";".join(users.values())
        users[address] = user
        queueList = b";".join(users[i][:2] + queueFlags[i] for i in queue)

        esend(self.sockets[address], b"INFO", self.passwords[address])
        esend(self.sockets[address], userList, self.passwords[address], 3)
        esend(self.sockets[address], queueList, self.passwords[address], 3)
        self.notify_lobby(b"+" + user)
        lobby.add(address)
        self.timeStamps[address] = time()
        logger.debug("L+%s (%d)" % (userToStr(user), len(lobby)))

    def notify_lobby(self, data):
        # Locals
        sockets = self.sockets
        passwords = self.passwords

        for address in self.lobby.copy():
            esend(sockets[address], data, passwords[address])

    def notify_games(self, data):
        # Locals
        sockets = self.sockets
        passwords = self.passwords

        for address in chain(*self.games.copy()):
            esend(sockets[address], data, passwords[address])

    def leave_lobby(self, address):
        self.lobby.remove(address)
        user = self.users[address]
        self.notify_lobby(b"-" + user[:2])
        self.queue.discard(address)
        self.queueFlags.pop(address, None)
        logger.debug("L-%s (%d)" % (userToStr(user), len(self.lobby)))

    def leave_games(self, address, goToLobby=True):
        # Locals
        games = self.games

        try:
            pair = next(pair for pair in games.copy() if address in pair)
        except StopIteration:
            return
        self.games.remove(pair)
        del self.gamesFlags[pair]
        logger.debug("%s stopped playing" % repr(pair))
        if address != pair[0]:
            pair = pair[::-1]
        if goToLobby:
            self.join_lobby(pair[0])
        self.join_lobby(pair[1])

    def leave(self, address):
        lobby = self.lobby
        if address in lobby:
            self.leave_lobby(address)
        elif address in self.sockets:
            self.leave_games(address, goToLobby=False)
        else:
            return
        try:
            self.sockets[address].close()
        except (ConnectionResetError, ConnectionAbortedError):
            pass
        user = self.users[address]
        # Clean variables
        del(self.sockets[address], self.passwords[address],
            self.users[address], self.timeStamps[address])
        self.pinged.discard(address)

        logger.info("-%s [%d]" % (user, len(lobby) + len(self.games) * 2))

    def run(self):
        def handle(socket, address):
            try:
                message = socket.recv(256)
            except (ConnectionResetError, ConnectionAbortedError):
                return
            decrypted = self.privateCipher.decrypt(message)
            password, rawName = decrypted[:PASS_SIZE], decrypted[PASS_SIZE:]
            name = "".join(chr(i) for i in rawName)[:NICKNAME_MAX_SIZE]
            esend(socket, b"RECEIVED", password)
            logger.debug("Received %s's (%s) password" % (name, address))

            socket.setblocking(False)
            self.sockets[address] = socket
            self.passwords[address] = password
            self.users[address] = self.freeIds.pop() + name.encode()
            userStr = userToStr(self.users[address])
            logger.info("+%s [%d]" %
                        (userStr, len(lobby) + len(self.games) * 2 + 1))
            self.join_lobby(address)
        s = newSocket()
        s.bind(self.address)
        s.listen(5)

        self.actions = deque()
        self.pinged = set()
        self.lobby = set()
        self.queue = set()
        self.queueFlags = dict()
        self.games = set()
        self.gamesFlags = dict()
        self.freeIds = set(i.to_bytes(2, "big") for i in range(1 << 16))
        # AddressInfo
        self.sockets = dict()
        self.passwords = dict()
        self.users = dict()
        self.timeStamps = dict()
        # Loops
        Thread(target=self.actions_loop, daemon=True).start()
        Thread(target=self.lobby_loop, daemon=True).start()
        Thread(target=self.games_loop, daemon=True).start()
        Thread(target=self.ping_loop, daemon=True).start()
        logger.info("Started all the loops")

        actions = self.actions
        lobby = self.lobby
        while True:
            socket, raw = s.accept()
            address = raw[0] + ":" + str(raw[1])
            if len(lobby) >= MAX_USERS:
                socket.close()
                logger.info("*%s size limit exceeded" % address)
            else:
                actions.append((handle, socket, address))

    def actions_loop(self):
        # Locals
        actions = self.actions

        while True:
            t0 = time()
            for values in actions.copy():
                values[0](*values[1:])
                actions.popleft()
            d = time() - t0
            if d > .1:
                logger.warn("Actions took %.3f seconds" % d)

    def lobby_loop(self):
        # Locals
        actions = self.actions
        lobby = self.lobby
        sockets = self.sockets
        passwords = self.passwords
        users = self.users
        pinged = self.pinged
        queue = self.queue
        queueFlags = self.queueFlags
        leave = self.leave
        games = self.games
        gamesFlags = self.gamesFlags
        leave_lobby = self.leave_lobby
        notify_lobby = self.notify_lobby

        while True:
            for address in lobby.copy():
                try:
                    size = int.from_bytes(sockets[address].recv(1), "big")
                    if not size:
                        logger.debug("%s chose to leave" % address)
                        raise ConnectionAbortedError
                except BlockingIOError:
                    continue
                except (ConnectionResetError, ConnectionAbortedError):
                    actions.append((leave, address))
                else:
                    data = decrypt(sockets[address].recv(size),
                                   passwords[address])
                    userStr = userToStr(users[address])
                    if data == b",":
                        pinged.discard(address)
                        logger.debug(".%s answered the ping (%d left)" %
                                     (userStr, len(pinged)))
                    elif data.startswith(b"?"):
                        message = b"?%s" % users[address][:2] + data[1:]
                        actions.append((notify_lobby, message))
                        if not data[1:]:
                            queue.discard(address)
                            queueFlags.pop(address, None)
                            logger.debug("%s deleted his queue" % userStr)
                        else:
                            queue.add(address)
                            queueFlags[address] = data[1:]
                            logger.debug("%s asked for a match: %s" %
                                         (userStr, str(data[1:])))
                    elif data.startswith(b"!"):
                        try:
                            opponent = next(i for i, j in list(users.items())
                                            if j.startswith(data[1:]))
                        except StopIteration:
                            logger.error(b"unknown user %s" % data[1:])
                            return
                        if opponent not in queue or opponent == address:
                            continue
                        flags = queueFlags[opponent]
                        pair = (opponent, address)
                        games.add(pair)
                        gamesFlags[pair] = flags
                        message = b"PLAY"
                        esend(sockets[address], message, passwords[opponent])
                        esend(sockets[opponent], message, passwords[opponent])
                        actions.append((leave_lobby, address))
                        actions.append((leave_lobby, opponent))
                        logger.debug("%s is playing against %s (%s)" %
                                     (userStr, userToStr(users[opponent]),
                                      flags))
                    else:
                        logger.warn("%s -> %s" % (userStr, str(data)))

    def games_loop(self):
        # Locals
        actions = self.actions
        games = self.games
        sockets = self.sockets
        passwords = self.passwords
        users = self.users
        leave = self.leave
        pinged = self.pinged

        while True:
            for pair in games.copy():
                for address, opponent in (pair, pair[::-1]):
                    try:
                        size = int.from_bytes(sockets[address].recv(1), "big")
                        if not size:
                            logger.debug("%s chose to leave" % address)
                            raise ConnectionAbortedError
                    except BlockingIOError:
                        continue
                    except (ConnectionResetError, ConnectionAbortedError):
                        actions.append((leave, address))
                        break
                    else:
                        data = decrypt(sockets[address].recv(size),
                                       passwords[address])
                        userStr = userToStr(users[address])
                        if data == b",":
                            pinged.discard(address)
                            logger.debug(".%s answered the ping (%d left)" %
                                         (userStr, len(pinged)))
                        else:
                            esend(sockets[opponent], data, passwords[opponent])
                            logger.warn("%s -> %s" % (userStr, str(data)))

    def ping_loop(self):
        # Locals
        actions = self.actions
        lobby = self.lobby
        games = self.games
        timeStamps = self.timeStamps
        pinged = self.pinged
        leave = self.leave
        notify_lobby = self.notify_lobby
        notify_games = self.notify_games

        while True:
            t0 = time()
            logger.debug(".Starting to clean pingers (%d)" % len(pinged))
            for address in pinged.copy():
                actions.append((leave, address))
            logger.debug(".Kicking afks (if any)")
            for address, timestamp in list(timeStamps.items()):
                if timestamp + AFK_RATE < t0 and address in lobby:
                    actions.append((leave, address))
            pinged.update(lobby)
            pinged.update(chain(*games))
            actions.append((notify_lobby, b"."))
            actions.append((notify_games, b"."))
            logger.debug(".PINGED")
            sleep(max(PING_RATE - time() + t0, 0))


if __name__ == "__main__":
    logger.info("Start")
    server = Server("TestServer", "localhost", 0xCE55)
    server.run()
