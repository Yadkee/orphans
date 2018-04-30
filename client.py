#! python3
from socket import socket
from threading import Thread

HOST = "localhost"
PORT = 9999


class Client():
    def __init__(self):
        self.s = socket()
        self.s.connect((HOST, PORT))
        t = Thread(target=self.listen, daemon=True)
        t.start()
        t.join()

    def listen(self):
        text = self.s.recv(4096)
        print(text)
        self.listen()

if __name__ == "__main__":
    c = Client()
