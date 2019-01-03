#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Crypto.Cipher import AES
from Crypto import Random
from math import ceil, log10
from hashlib import sha512, sha256


def _bytes(i, lenght=None):
    if lenght is None:
        lenght = log10(len(i)) // log10(256)
    int_list = []
    for _ in range(lenght):
        int_list.insert(0, i & 255)
        i >>= 8
    return bytes(int_list)


def _int(b):
    result = 0
    for i in b:
        result <<= 8
        result += i
    return result


def pad(data, block_size, fill=bytes(1)):
    return data.ljust(block_size - len(data) % block_size, fill)


class Cipher():
    def __init__(self, key=None):
        self.header = b"_ENCRYPTED DATA_"
        self.null = bytes(1)
        self.sizeLenght = 5
        self.key = key

    def encrypt(self, data):
        if not data.startswith(self.header):
            key = sha256(self.key).digest()
            iv = Random.new().read(AES.block_size)
            obj = AES.new(key, AES.MODE_CBC, iv)

            size = _bytes(len(data), self.sizeLenght)
            padded = size + data + self.null * \
                (AES.block_size - (len(size) + len(data)) % AES.block_size)

            return self.header + iv + sha512(self.key).digest() + obj.encrypt(padded)
        else:
            print("Data is already encrypted")
            return data

    def decrypt(self, data):
        if data.startswith(self.header):
            keySha = data[len(self.header) + AES.block_size:][:64]
            if keySha == sha512(self.key).digest():
                key = sha256(self.key).digest()
                iv = data[len(self.header):][:AES.block_size]
                obj = AES.new(key, AES.MODE_CBC, iv)

                padded = obj.decrypt(
                    data[len(self.header) + AES.block_size + 64:])
                size = _int(padded[:self.sizeLenght])

                return padded[self.sizeLenght:][:size]
            else:
                print("They key used is not correct")
                return None
        else:
            print("Data is not encrypted")
            return data
