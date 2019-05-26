#! python3
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto import Random


class Secure():
    def __init__(self):
        random_generator = Random.new().read
        self.privateKey = RSA.generate(2048, random_generator)
        self.publicKey = self.privateKey.publickey()
        self.privateCipher = PKCS1_OAEP.new(self.privateKey)

    def fromDer(self, data):
        return RSA.importKey(data)

    def cipher(self, publicKey, data):
        publicCipher = PKCS1_OAEP.new(publicKey)
        return publicCipher.encrypt(data)
