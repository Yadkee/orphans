#! python3
# Pi digits finder. Finds 5481 digits in 719 seconds with a precision of 10000 decimals.
from decimal import Decimal, getcontext
from functools import lru_cache
from itertools import count
from math import sqrt
from sys import setrecursionlimit
from time import time

D0 = Decimal(0)
D1 = Decimal(1)
D2 = Decimal(2)
setrecursionlimit(1 << 20)


@lru_cache(maxsize=1 << 20)
def cos_180_n(n):
    if n == 1:
        return D0
    return ((D1 + cos_180_n(n - 1)) / D2).sqrt()


def sen_180_n(n):
    return (D1 - cos_180_n(n - 1) ** D2).sqrt()


def pi(n):
    return 2 ** (n - 1) * sen_180_n(n)


def furthest(m, n):
    getcontext().prec = m
    cos_180_n.cache_clear()
    prev = 0
    l = []
    for i in count(n):
        print("\r%d..." % i, end="")
        p = pi(i)
        if p < prev:
            l.append((p, i - 1))
            if len(l) == 5:
                print("\r", end="")
                return sum(j[0] for j in l) / 5, l[-1][1]
        prev = p


def finder(m, n):
    with open("pi.txt") as f:
        truePi = f.read()
    for mi in count(m):
        t0 = time()
        p, n = furthest(mi, n - 20)
        print("Polygon of 2^%d sides with a precision of %d" % (n, mi))
        print(sum(1 for i, j in zip(truePi, str(p)) if i == j),
              "Digits of Pi are right in %d seconds" % (time() - t0))


finder(1000, 500)
