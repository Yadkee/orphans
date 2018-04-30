#! python3
from socket import socket
from threading import Thread

HOST = "localhost"
PORT = 9999


class Server():
    def __init__(self):
        self.s = socket()
        self.s.bind((HOST, PORT))
        self.s.listen(5)
        self.clients = []
        Thread(target=self.accept, daemon=True).start()
        Thread(target=self.listen, daemon=True).start()

    def accept(self):
        socket, adress = self.s.accept()
        socket.settimeout(0)
        socket.send("Welcome {}\n".format(adress).encode())
        print(adress, "joined")
        self.clients.append((socket, adress))
        self.accept()

    def listen(self):
        while True:
            for client, adress in self.clients:
                try:
                    try:
                        text = client.recv(4096)
                        print(text)
                    except BlockingIOError:
                        pass
                except (ConnectionResetError, ConnectionAbortedError):
                    self.clients.remove((client, adress))
                    print(adress, "left")


if __name__ == "__main__":
    s = Server()
    while True:
        pass
