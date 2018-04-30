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
        Thread(target=self.accept, daemon=True).start()
        Thread(target=self.listen, daemon=True).start()

    def accept(self):
        while True:
            socket, adress = self.s.accept()
            socket.settimeout(0)
            socket.send(b">>>" + self.secure.publicKey.exportKey("DER"))
            print("Sent public key to", adress)
            self.clients.append((socket, adress))

    def handle(self, data, client, adress):
        if data.startswith(b">>>"):
            print("Received public key from", adress)
            self.clientKeys[adress] = self.secure.fromDer(data[3:])
            self.clientCiphers[adress] = PKCS1_OAEP.new(self.clientKeys[adress])
            self.send(b"Welcome", client, adress)
            print("Welcomed", adress)
        else:
            deciphered = self.secure.privateCipher.decrypt(data)
            if deciphered == b"PONG":
                self.haveNotPong.remove((client, adress))
                print(adress, "did a pong")
            else:
                print(deciphered, adress)

    def send(self, data, client, adress):
        ciphered = self.clientCiphers[adress].encrypt(data)
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
                        self.send(b"PING", client, adress)
                except (ConnectionResetError, ConnectionAbortedError):
                    self.clients.remove((client, adress))
                    print(adress, "left")
            if ping:
                self.lastPing = time()
                # TODO: Remove people who haven't pong yet before updating.
                self.haveNotPong.update(self.clients)


if __name__ == "__main__":
    s = Server()
    while True:
        pass
