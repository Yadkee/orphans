#! python3
from Crypto.PublicKey import RSA
from Crypto.Cipher import (PKCS1_OAEP, AES)
from Crypto import Random

PASS_SIZE = 16  # Client's AES symmetric password
NONCE_SIZE = 8
random = Random.new()


def rsa():
    privateKey = RSA.generate(2048, random.read)
    publicKey = privateKey.publickey().exportKey("DER")
    privateCipher = PKCS1_OAEP.new(privateKey)
    return publicKey, privateCipher


def fromDer(data):
    return PKCS1_OAEP.new(RSA.importKey(data))


def generate_password(size):
    return random.read(size)


def encrypt(data, password):
    nonce = random.read(NONCE_SIZE)
    aes = AES.new(password, AES.MODE_CTR, nonce=nonce)
    return nonce + aes.encrypt(data)


def decrypt(data, password):
    nonce = data[:NONCE_SIZE]
    aes = AES.new(password, AES.MODE_CTR, nonce=nonce)
    return aes.decrypt(data[NONCE_SIZE:])
