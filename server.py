#! python3
from socket import socket as _socket
from threading import Thread
from time import time
from secure import Secure
from Crypto.Cipher import PKCS1_OAEP

HOST = "localhost"
PORT = 9999


class Server():
    def __init__(self):
        self.s = _socket()
        self.s.bind((HOST, PORT))
        self.s.listen(5)
        self.clients = []
        self.clientKeys = {}
        self.clientCiphers = {}
        self.lastPing = time()
        self.haveNotPong = set()
        self.secure = Secure()
        self.matches = []
        Thread(target=self.accept, daemon=True).start()
        Thread(target=self.listen, daemon=True).start()

    def accept(self):
        while True:
            socket, adress = self.s.accept()
            socket.settimeout(0)
            socket.send(b">>>" + self.secure.publicKey.exportKey("DER"))
            print("Sent server key to", adress)
            self.clients.append((socket, adress))

    def handle(self, data, client, adress):
        if data.startswith(b">>>"):
            print("Received client key from", adress)
            self.clientKeys[client] = self.secure.fromDer(data[3:])
            self.clientCiphers[client] = PKCS1_OAEP.new(self.clientKeys[client])
            self.send(b"Welcome", client)
            if len(self.clientCiphers) == 2:
                pair = []
                color = b"WHITE"
                for c, a in self.clients:
                    if c in self.clientCiphers:
                        self.send(b"MATCH" + color, c)
                        pair.append(c)
                        color = b"BLACK"
                self.matches.append(pair)
            print("Welcomed", adress)
        else:
            deciphered = self.secure.privateCipher.decrypt(data)
            if not deciphered.startswith(b">>"):
                print("Invalid packet from", adress)
                return
            deciphered = deciphered[2:]
            if deciphered == b"PONG":
                self.haveNotPong.remove((client, adress))
                print(adress, "answered a ping with a pong")
            elif (deciphered.startswith(b"MOVE") or
                  deciphered.startswith("CASTLE")):
                for i in self.matches:
                    if client in i:
                        c1, c2 = i
                        adversary = c2 if c1 == client else c1
                        self.send(deciphered, adversary)
                        break
            else:
                print(deciphered, adress)

    def send(self, data, client):
        ciphered = self.clientCiphers[client].encrypt(b">>" + data)
        client.send(ciphered)

    def listen(self):
        while True:
            ping = time() > self.lastPing + 30
            for client, adress in self.clients:
                try:
                    try:
                        data = client.recv(4096)
                    except BlockingIOError:
                        pass
                    else:
                        self.handle(data, client, adress)
                    if ping:
                        self.send(b"PING", client)
                except (ConnectionResetError, ConnectionAbortedError):
                    self.clients.remove((client, adress))
                    del self.clientKeys[client]
                    del self.clientCiphers[client]
                    print(adress, "left")
            if ping:
                print("Pinged every client (%d)" % len(self.clients))
                self.lastPing = time()
                # TODO: Remove people who haven't pong yet before updating.
                self.haveNotPong.update(self.clients)


if __name__ == "__main__":
    s = Server()
    while True:
        pass
