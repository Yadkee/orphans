#! python3
# Five programming problems that every software engineer should be able to solve in less than 1 hour.
# https://www.shiftedup.com/2015/05/07/five-programming-problems-every-software-engineer-should-be-able-to-solve-in-less-than-1-hour
from itertools import permutations


def f1(l):
    def r(l, t=0):
        if not l:
            return t
        return r(l[1:], t + l[0])
    t3 = r(l)

    t1 = 0
    for i in l:
        t1 += i

    t2 = 0
    i = 0
    while i < len(l):
        t2 += l[i]
        i += 1

    return (t1, t2, t3)


def f2(l1, l2):
    return [k for i, j in zip(l1, l2) for k in (i, j)]


def f3():
    out = []
    a, b = 0, 1
    for _ in range(100):
        out.append(a)
        a, b = b, b + a
    return out


def f4(l):
    strings = map(str, l)
    iterable = ("".join(i) for i in permutations(strings))
    return max(iterable, key=int)


def f5():
    def r(s, i):
        if i == 10:
            if eval(s) == 100:
                yield s
            return
        for j in ("+", "-", ""):
            yield from r(s + j + str(i), i + 1)
    return "\n".join(r("1", 2))


print(f1([3, 2, 5]))
print(f2([1, 2, 3], [9, 8, 7]))
print(f3())
print(f4([50, 2, 1, 9]))
print(f5())
