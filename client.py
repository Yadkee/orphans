#! python3
from socket import socket
from threading import Thread
from secure import Secure
from Crypto.Cipher import PKCS1_OAEP

HOST = "localhost"
PORT = 9999


class Client():
    def __init__(self, listenCallback):
        self.listenCallback = listenCallback
        self.s = socket()
        self.s.connect((HOST, PORT))
        self.secure = Secure()
        self.serverKey = None
        Thread(target=self.listen, daemon=True).start()

    def listen(self):
        while True:
            data = self.s.recv(4096)
            if data.startswith(b">>>"):
                print("Received server key")
                self.serverKey = self.secure.fromDer(data[3:])
                self.serverCipher = PKCS1_OAEP.new(self.serverKey)
                self.s.send(b">>>" + self.secure.publicKey.exportKey("DER"))
                print("Sent own key")
            else:
                deciphered = self.secure.privateCipher.decrypt(data)
                if not deciphered.startswith(b">>"):
                    print("Invalid packet from server")
                    return
                deciphered = deciphered[2:]
                if deciphered == b"PING":
                    self.send(b"PONG")
                    print("PING -> PONG")
                else:
                    self.listenCallback(deciphered)
                    print(deciphered)

    def send(self, data):
        ciphered = self.serverCipher.encrypt(b">>" + data)
        self.s.send(ciphered)

if __name__ == "__main__":
    from main import run
    run()
