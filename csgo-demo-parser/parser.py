#! python3
"""
https://developer.valvesoftware.com/wiki/DEM_Format#Demo_Header
http://hg.alliedmods.net/hl2sdks/hl2sdk-css/file/1901d5b74430/public/demofile/demoformat.h
https://github.com/saul/demofile/blob/master/demo.js
https://wiki.alliedmods.net/Counter-Strike:_Global_Offensive_Events
https://developers.google.com/protocol-buffers/docs/encoding
https://gitlab.ksnetwork.es/snippets/8
https://github.com/andreas-mausch/csgo-demohighlights/blob/master/source/csgo-demolibrary/parser/Stringtable.cpp
dem_signon 	1
dem_packet 	2
dem_synctick 	3
dem_consolecmd 	4
dem_usercmd 	5
dem_datatables 	6
dem_stop 	7
dem_stringtables 	9
La información para la fórmula de Rating es:
- Kills per Round
=(Kills/Rounds)/0.679
- Survived Rounds
=((Rounds-Deaths)/Rounds)/0.317
- Multikill Rating
=((1K+(4*2K)+(9*3K)+(16*4K)+ (25*5K))/Rounds)/1.277
"""
import struct
from collections import namedtuple
from collections import OrderedDict
from collections import deque
from itertools import count
from time import time
from string import digits, ascii_letters, punctuation
from pprint import pprint
from math import ceil
from math import log2

I = struct.Struct("<i")
UI = struct.Struct("<I")
F = struct.Struct("<f")

ABC = {ord(i) for i in (digits + ascii_letters + punctuation + " ")}


def decode(b):
    return "".join(chr(i) for i in b if i in ABC)


class ByteStream():
    def __init__(self, data):
        self.offset = 0
        self.b = data
        self.size = len(self.b)
        self.caps = deque([self.size])
        self.activeCap = self.caps[0]

    def __iter__(self):
        return self

    def __next__(self):
        if self.can_iterate():
            value = self.readVarInt()
            return (value >> 3, value & 7)  # Field, type
        else:
            raise StopIteration

    @property
    def left(self):
        return self.b[self.offset:self.activeCap]

    def cap(self, offset):
        """Defines a cap in offset bytes"""
        self.caps.appendleft(self.offset + offset)
        self.activeCap = self.caps[0]

    def capI(self):
        self.cap(self.readUInt32())

    def capV(self):
        self.cap(self.readVarInt())

    def release(self):
        """Releases last cap"""
        self.caps.popleft()
        self.activeCap = self.caps[0]

    def can_iterate(self):
        return self.offset < self.activeCap

    def readByte(self):
        value = self.b[self.offset]
        self.offset += 1
        return value

    def readInt32(self):
        value = I.unpack_from(self.b, self.offset)[0]
        self.offset += I.size
        return value

    def readUInt32(self):
        value = UI.unpack_from(self.b, self.offset)[0]
        self.offset += UI.size
        return value

    def readFloat(self):
        value = F.unpack_from(self.b, self.offset)[0]
        self.offset += F.size
        return value

    def readVarInt(self):
        value = 0
        for i in count():
            d = self.readByte()
            value |= (d & 0x7f) << (7 * i)
            if not d & 0x80:
                break
        return value

    def readBytes(self, n):
        value = self.b[self.offset:self.offset + n]
        self.offset += n
        return value

    def readIBytes(self):
        return self.readBytes(self.readUInt32())

    def readVBytes(self):
        return self.readBytes(self.readVarInt())

    def readIString(self):
        return decode(self.readIBytes())

    def readVString(self):
        return decode(self.readVBytes())

    def undo(self, offset):
        self.offset -= offset

    def skip(self, offset):
        self.offset += offset

    def skipI(self):
        self.skip(self.readUInt32())

    def skipV(self):
        self.skip(self.readVarInt())

    def skipC(self):
        """Skip until cap"""
        self.skip(self.activeCap - self.offset)


class BitStream():
    def __init__(self, data):
        self.offset = 0
        self.b = data
        self.size = len(self.b) * 8

    def readBit(self):
        b, o = divmod(self.offset, 8)
        self.offset += 1
        return bool(self.b[b] & (1 << o))

    def readBits(self, offset):
        b0, o0 = divmod(self.offset, 8)
        b1, o1 = divmod(self.offset + offset, 8)
        if b1 == b0:
            return [self.b[b0] & ~(0xFF << (8 - o0)) & ~(0xFF >> o1)]
        return (self.b[b0] & ~(0xFF << (8 - o0)), self.b[b0 + 1:b1],
                self.b[b1] & ~(0xFF >> o1))

    def readUBits(self, offset):
        return sum(i << (8 * a) for a, i in enumerate(
                reversed(self.readBits(offset))))


class Table():
    def __init__(self, name, maxEntries, userDataSize, userDataFixedSize):
        self.name = name
        self.maxEntries = maxEntries
        self.userDataSize = userDataSize
        self.userDataFixedSize = userDataFixedSize

    def parse(self, numEntries, stringData):
        """var PlayerInfo = new Parser()
        .endianess('big')
        .uint32('unknown_lo')
        .uint32('unknown_hi')
        .uint32('xuid_lo')
        .uint32('xuid_hi')
        .string('name', {length: consts.MAX_PLAYER_NAME_LENGTH, stripNull: true})
        .int32('userId')
        .string('guid', {length: consts.SIGNED_GUID_LEN + 1, stripNull: true})
        .skip(3)
        .uint32('friendsId')
        .string('friendsName', {length: consts.MAX_PLAYER_NAME_LENGTH, stripNull: true})
        .uint8('fakePlayer', {formatter: x => x !== 0})
        .skip(3)
        .uint8('isHltv', {formatter: x => x !== 0})
        .skip(3)
        .array('customFiles', {
            type: 'uint32be',
            length: consts.MAX_CUSTOM_FILES
        });"""
        return  # INCOMPLETE CODE
        stream = BitStream(stringData)
        assert not stream.readBit(), "dictionary encoding unsupported"
        maxEntries = self.maxEntries
        entryBits = ceil(log2(maxEntries))
        entryIndex = -1
        for i in range(numEntries):
            if not stream.readBit():
                entryIndex = stream.readUBits(entryBits)
            else:
                entryIndex += 1
        # print(numEntries, stringData)


class Game():
    headerFormat = "<8s2i260s260s260s260sf3i"
    headerKeys = ["Header", "Demo_Protocol", "Network_Protocol", "Server_name",
                  "Client_name", "Map_name", "Game_directory", "Playback_time",
                  "Playback_ticks", "Playback_rames", "Sign_on_length"]
    Header = namedtuple("Header", headerKeys)
    headerStruct = struct.Struct(headerFormat)

    def __init__(self, data):
        unpackedValues = self.headerStruct.unpack_from(data)
        self.header = self.Header(*unpackedValues)._asdict()
        self.buffer = ByteStream(data[self.headerStruct.size:])
        self.tables = []
        self.convars = {}

    @property
    def progress(self):
        return "%02d%s" % (self.buffer.offset * 100 // self.buffer.size, "%")

    def table_index_by_name(self, name):
        for a, i in enumerate(self.tables):
            if i.name == name:
                return a
        return -1

    def print_header(self):
        for i, j in self.header.items():
            if isinstance(j, bytes):
                j = j.strip(b"\x00")
            print("%16s: %s" % (i, j))

    def parse_packet(self):
        # Avoid dots (Optimization)
        chunk = self.buffer
        chunk.capI()
        can_iterate = chunk.can_iterate
        crvi = chunk.readVarInt
        crvb = chunk.readVBytes
        csv = chunk.skipV
        ccv = chunk.capV
        crel = chunk.release
        # In order of times called (^ to v):
        # 13 4 26 25 17 27 23 28 6 12 5 7 8 10 14 18 30
        # s    o  e     o  m       s                 e
        # s->stringtables  o->entities
        # e->events        m->messages
        while can_iterate():
            cmd = crvi()
            if cmd == 13:  # svc_UpdateStringTable
                ccv()
                for f, _ in chunk:
                    if f == 1:
                        tableId = crvi()
                    elif f == 2:
                        numChangedEntries = crvi()
                    elif f == 3:
                        stringData = crvb()
                table = self.tables[tableId]
                table.parse(numChangedEntries, stringData)
                crel()
            elif cmd == 12:  # svc_CreateStringTable
                ccv()
                for f, _ in chunk:
                    if f == 1:
                        name = decode(crvb())
                    elif f == 2:
                        maxEntries = crvi()
                    elif f == 3:
                        numEntries = crvi()
                    elif f == 4:
                        userDataFixedSize = crvi()
                    elif f == 5:
                        userDataSize = crvi()
                    elif f == 6:
                        userDataSizeBits = crvi()
                    elif f == 7:
                        flags = crvi()
                    elif f == 8:
                        stringData = crvb()
                table = Table(name, maxEntries, userDataSize,
                              userDataFixedSize)
                self.tables.append(table)
                table.parse(numEntries, stringData)
                crel()
            else:
                csv()
            # message = ByteStream(chunk.readVBytes())
        crel()

    def parse_game(self):
        # Avoid dots (Optimization)
        data = self.buffer
        can_iterate = data.can_iterate
        drb = data.readByte
        ds = data.skip
        spp = self.parse_packet
        while can_iterate():
            f = drb()
            if f == 2 or f == 1:  # dem_packet and dem_signon
                ds(165)  # 160 + tick(4) + slot(1)
                spp()
            elif f == 6:  # dem_datatables
                ds(5)  # tick(4) + slot(1)
                data.skipI()
                # chunk = ByteStream(self.buffer.readIBytes())
            elif f == 7:  # dem_stop
                tick = data.readInt32()
                print("Ended at tick %d on offset %d" % (tick, data.offset))
                break
            elif f == 9:  # dem_stringtables
                ds(5)  # tick(4) + slot(1)
                data.skipI()
                # chunk = ByteStream(self.buffer.readIBytes())
            elif f == 3:
                ds(5)  # tick(4) + slot(1)
            else:  # Ignoring dem_synctick
                tick = data.readInt32()
                slot = drb()
                print("\n- %d; [%d] at tick %d on slot %d" %
                      (data.offset, f, tick, slot))
                raise Exception


def main():
    t0 = time()
    path = "90_unik-leadores_de_train.dem"
    # path = "ksn-onlyheroes-rov_gaming day-de_train.dem"
    # path = "ksn-blackclaw_cs_go-plägue-de_overpass.dem"
    # path = "ksn-neutralize-pure_gamers-de_overpass.dem"
    # path = "ksn-hero-roxter_gaming-de_cbble.dem"
    path = "ksn-x6tence_academy-ex godlike-de_mirage.dem"
    with open(path, "rb") as f:
        data = f.read()
    game = Game(data)
    game.print_header()
    game.parse_game()
    print("Took %.4f seconds" % (time() - t0))


if __name__ == "__main__":
    main()
