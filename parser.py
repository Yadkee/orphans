#! python3
"""
https://developer.valvesoftware.com/wiki/DEM_Format#Demo_Header
http://hg.alliedmods.net/hl2sdks/hl2sdk-css/file/1901d5b74430/public/demofile/demoformat.h
https://github.com/saul/demofile/blob/master/demo.js
https://wiki.alliedmods.net/Counter-Strike:_Global_Offensive_Events
https://developers.google.com/protocol-buffers/docs/encoding
https://gitlab.ksnetwork.es/snippets/8
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
from itertools import count
from time import time
from string import digits, ascii_letters, punctuation

I = struct.Struct("<i")
UI = struct.Struct("<I")
F = struct.Struct("<f")

ABC = {ord(i) for i in (digits + ascii_letters + punctuation + " ")}


def decode(b):
    return "".join(chr(i) for i in b if i in ABC)


class Buffer():
    def __init__(self, *arg, **kw):
        self.offset = 0
        self.b = bytes(*arg, **kw)
        self.size = len(self.b)

    def __iter__(self):
        return self

    def __next__(self):
        if self.canIterate:
            value = self.readVarInt()
            return (value >> 3, value & 7)  # Field, type
        else:
            raise StopIteration

    @property
    def canIterate(self):
        return self.offset < self.size

    @property
    def difference(self):
        return self.size - self.offset

    @property
    def left(self):
        return self.b[self.offset:]

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

    def skipIbytes(self):
        self.skip(self.readUInt32())


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
        self.buffer = Buffer(data[self.headerStruct.size:])
        self.tables = {}
        self.convars = {}

        self.print_header()
        self.parse()

    def print_header(self):
        for i, j in self.header.items():
            if isinstance(j, bytes):
                j = j.strip(b"\x00")
            print("%16s: %s" % (i, j))

    @property
    def progress(self):
        return self.buffer.offset * 100 // self.buffer.size

    def handle_signon(self):
        data = self.buffer
        # OriginViewAngles 1 (76)
        #  flags (4)
        #  original(36) [vector, angle, angle]
        #  resampled(36) [vector, angle, angle]
        # OriginViewAngles 2 (76)
        # ServerFrame and ClientFrame (8) (could get ping from delta)
        # In GOTV ping is always 0
        data.skip(160)
        chunk = Buffer(data.readIBytes())
        while chunk.canIterate:
            cmd = chunk.readVarInt()
            message = Buffer(chunk.readVBytes())
            mrvi = message.readVarInt
            mrvb = message.readVBytes
            event = OrderedDict()
            if cmd == 4:  # net_Tick
                continue
                event["type"] = "net_Tick"
                for f, t in message:
                    if f == 1:
                        event["tick"] = mrvi()
                    elif f == 4:
                        event["host_computationtime"] = mrvi()
                    elif f == 5:
                        event["host_computationtime_std_deviation"] = mrvi()
                    elif f == 6:
                        event["host_framestarttime_std_deviation"] = mrvi()
                    elif f == 7:
                        event["hltv_replay_flags"] = mrvi()
                    else:
                        print(cmd, f, t)
                # optional uint32 tick = 1;
                # optional uint32 host_computationtime = 4;
                # optional uint32 host_computationtime_std_deviation = 5;
                # optional uint32 host_framestarttime_std_deviation = 6;
                # optional uint32 hltv_replay_flags = 7;
            elif cmd == 5:  # net_StringCmd
                continue
                event["type"] = "net_StringCmd"
                for f, t in message:
                    if f == 1:
                        event["command"] = decode(mrvb())
                    else:
                        print(cmd, f, t)
                # optional string command = 1;
            elif cmd == 6:  # net_SetConVar
                continue
                event["type"] = "net_SetConVar"
                for f, t in message:
                    if f == 1:
                        _ = mrvi()  # 0 idea of what is this
                        event["convars"] = []
                        for f2, t2 in message:
                            _ = mrvi()  # 0 idea of what is this
                            if f2 == 1:
                                cvar = OrderedDict()
                                for f3, t3 in message:
                                    if f3 == 1:
                                        cvar["name"] = decode(mrvb())
                                    elif f3 == 2:
                                        cvar["value"] = decode(mrvb())
                                    elif f3 == 3:
                                        cvar["dictionary_name"] = mrvi()
                                    else:
                                        print(" ", cmd, f2, t2)
                                event["convars"].append(cvar)
                                try:
                                    self.convars[cvar["name"]] = cvar["value"]
                                except KeyError:
                                    print(cmd, cvar)
                            else:
                                print("", cmd, f2, t2)
                    else:
                        print(cmd, f, t)
                # CMsg_CVars.Cvar:
                #  optional string name = 1;
                #  optional string value = 2;
                #  optional uint32 dictionary_name = 3;
                # CMsg_CVars:
                #  repeated .CMsg_CVars.CVar cvars = 1;
                # optional .CMsg_CVars convars = 1;
            elif cmd == 7:  # net_SignonState
                continue
                event["type"] = "net_SignonState"
                event["players_networkids"] = []
                for f, t in message:
                    if f == 1:
                        event["signon_state"] = mrvi()
                    elif f == 2:
                        event["spawn_count"] = mrvi()
                    elif f == 3:
                        event["num_server_players"] = mrvi()
                    elif f == 4:
                        event["player_networkids"].append(decode(mrvb()))
                    elif f == 5:
                        event["map_name"] = decode(mrvb())
                # optional uint32 signon_state = 1;
                # optional uint32 spawn_count = 2;
                # optional uint32 num_server_players = 3;
                # repeated string players_networkids = 4;
                # optional string map_name = 5;
            elif cmd == 8:  # svc_ServerInfo
                continue
                event["type"] = "svc_ServerInfo"
                for f, t in message:
                    if f == 1:
                        event["protocol"] = mrvi()
                    elif f == 2:
                        event["server_count"] = mrvi()
                    elif f == 3:
                        event["is_dedicated"] = mrvi()
                    elif f == 4:
                        event["is_official_valve_server"] = mrvi()
                    elif f == 5:
                        event["is_hltv"] = mrvi()
                    elif f == 6:
                        event["is_replay"] = mrvi()
                    elif f == 21:
                        event["is_redirecting_to_proxy_relay"] = mrvi()
                    elif f == 7:
                        event["c_os"] = mrvi()
                    elif f == 8:
                        event["map_crc"] = message.readUInt32()
                    elif f == 9:
                        event["client_crc"] = message.readUInt32()
                    elif f == 10:
                        event["string_table_crc"] = message.readUInt32()
                    elif f == 11:
                        event["max_clients"] = mrvi()
                    elif f == 12:
                        event["max_classes"] = mrvi()
                    elif f == 13:
                        event["player_slot"] = mrvi()
                    elif f == 14:
                        event["tick_interval"] = message.readFloat()
                    elif f == 15:
                        event["game_dir"] = decode(mrvb())
                    elif f == 16:
                        event["map_name"] = decode(mrvb())
                    elif f == 17:
                        event["map_group_name"] = decode(mrvb())
                    elif f == 18:
                        event["sky_name"] = decode(mrvb())
                    elif f == 19:
                        event["host_name"] = decode(mrvb())
                    elif f == 20:
                        event["public_ip"] = mrvi()
                    elif f == 22:
                        event["ugc_map_id"] = mrvi()
                        message.skip(1)
                    else:
                        print(cmd, f, t)
                # optional int32 protocol = 1;
                # optional int32 server_count = 2;
                # optional bool is_dedicated = 3;
                # optional bool is_official_valve_server = 4;
                # optional bool is_hltv = 5;
                # optional bool is_replay = 6;
                # optional bool is_redirecting_to_proxy_relay = 21;
                # optional int32 c_os = 7;
                # optional fixed32 map_crc = 8;
                # optional fixed32 client_crc = 9;
                # optional fixed32 string_table_crc = 10;
                # optional int32 max_clients = 11;
                # optional int32 max_classes = 12;
                # optional int32 player_slot = 13;
                # optional float tick_interval = 14;
                # optional string game_dir = 15;
                # optional string map_name = 16;
                # optional string map_group_name = 17;
                # optional string sky_name = 18;
                # optional string host_name = 19;
                # optional uint32 public_ip = 20;
                # optional uint64 ugc_map_id = 22;"""
            elif cmd == 10:  # svc_ClassInfo
                continue
                event["type"] = "svc_ClassInfo"
            elif cmd == 12:  # svc_CreateStringTable
                continue
                event["type"] = "svc_CreateStringTable"
                for f, t in message:
                    if f == 1:
                        event["name"] = decode(mrvb()) 
                    elif 2 <= f <= 7:
                        event[f] = mrvi()
                    elif f == 8:
                        event["string_data"] = mrvb()
                    else:
                        print(cmd, f, t)
                try:
                    self.tables[event["name"]] = event["string_data"]
                except KeyError:
                    print(cmd, event)
                # optional string name = 1;
                # optional int32 max_entries = 2;
                # optional int32 num_entries = 3;
                # optional bool user_data_fixed_size = 4;
                # optional int32 user_data_size = 5;
                # optional int32 user_data_size_bits = 6;
                # optional int32 flags = 7;
                # optional bytes string_data = 8;
            elif cmd == 13:  # svc_UpdateStringTable
                continue
                event["type"] = "svc_UpdateStringTable"
                for f, t in message:
                    if f == 1:
                        event["table_id"] = mrvi()
                    elif f == 2:
                        event["num_changed_entries"] = mrvi()
                    elif f == 3:
                        event["string_data"] = mrvb()
                    else:
                        print(cmd, f, t)
                try:
                    key = tuple(self.tables.keys())[event["table_id"]]
                    self.tables[key] = event["string_data"]
                except KeyError:
                    print(cmd, event)
                # optional int32 table_id = 1;
                # optional int32 num_changed_entries = 2;
                # optional bytes string_data = 3;
            elif cmd == 14:  # svc_VoiceInit
                continue
                event["type"] = "svc_VoiceInit"
                for f, t in message:
                    if f == 1:
                        event["quality"] = mrvi()
                    elif f == 2:
                        event["codec"] = decode(mrvb())
                    elif f == 3:
                        event["version"] = mrvi()
                    else:
                        print(cmd, f, t)
                print(event)
                # optional int32 quality = 1;
                # optional string codec = 2;
                # optional int32 version = 3 [default = 0];
            elif cmd == 17:  # svc_Sounds
                continue
                event["type"] = "svc_Sounds"
            elif cmd == 18:  # svc_SetView
                continue
                event["type"] = "svc_SetView"
                for f, t in message:
                    if f == 1:
                        event["entity_index"] = mrvi()
                    else:
                        print(cmd, f, t)
                # optional int32 entity_index = 1;
            elif cmd == 23:  # svc_UserMessage
                continue
                event["type"] = "svc_UserMessage"
                for f, t in message:
                    if f == 1:
                        msgType = mrvi()
                        event["msg_type"] = msgType
                    elif f == 2:
                        event["msg_data"] = mrvb()
                    elif f == 3:
                        event["passthrough"] = mrvi
                    else:
                        print(cmd, f, t)
                # optional int32 msg_type = 1;
                # optional bytes msg_data = 2;
                # optional int32 passthrough = 3;
                parsed = OrderedDict()
                msgData = Buffer(event["msg_data"])
                drvi = msgData.readVarInt
                drvb = msgData.readVBytes
                if msgType == 5:  # CS_UM_SayText
                    parsed["type"] = "CS_UM_SayText"
                    for f, t in msgData:
                        if f == 1:
                            parsed["ent_idx"] = drvi()
                        elif f == 2:
                            parsed["text"] = decode(drvb())
                        elif f == 3:
                            parsed["chat"] = drvi()
                        elif f == 4:
                            parsed["textallchat"] = drvi()
                        else:
                            print(cmd, msgType, f, t)
                    # optional int32 ent_idx = 1;
                    # optional string text = 2;
                    # optional bool chat = 3;
                    # optional bool textallchat = 4;
                elif msgType == 6:  # CS_UM_SayText2
                    parsed["type"] = "CS_UM_SayText2"
                    parsed["params"] = []
                    for f, t in msgData:
                        if f == 1:
                            parsed["ent_idx"] = drvi()
                        elif f == 2:
                            parsed["chat"] = drvi()
                        elif f == 3:
                            parsed["msg_name"] = decode(drvb())
                        elif f == 4:
                            parsed["params"].append(decode(drvb()))
                        elif f == 5:
                            parsed["textallchat"] = drvi()
                        else:
                            print(cmd, msgType, f, t)
                    # optional int32 ent_idx = 1;
                    # optional bool chat = 2;
                    # optional string msg_name = 3;
                    # repeated string params = 4;
                    # optional bool textallchat = 5;
                elif msgType == 7:  # CS_UM_TextMsg
                    parsed["type"] = "CS_UM_TextMsg"
                    parsed["params"] = []
                    for f, t in msgData:
                        if f == 1:
                            parsed["msg_dst"] = drvi()
                        elif f == 3:
                            parsed["params"].append(decode(drvb()))
                        else:
                            print(cmd, msgType, f, t)
                    # optional int32 msg_dst = 1;
                    # repeated string params = 3;
                elif msgType == 12:  # CS_UM_Shake
                    parsed["type"] = "CS_UM_Shake"
                    # optional int32 command = 1;
                    # optional float local_amplitude = 2;
                    # optional float frequency = 3;
                    # optional float duration = 3;
                elif msgType == 21:  # CS_UM_Damage
                    parsed["type"] = "CS_UM_Damage"
                    for f, t in msgData:
                        if f == 1:
                            parsed["amount"] = drvi()
                        elif f == 2:
                            _ = drvi()
                            vector = []
                            for f2, t2 in msgData:
                                if t2 != 5:
                                    msgData.undo(1)
                                    break
                                if 1 <= f2 <= 3:
                                    vector.append(msgData.readFloat())
                                else:
                                    print("", cmd, msgType, f2, t2)
                            parsed["inflictor_world_pos"] = vector
                        elif f == 3:
                            parsed["victim_entindex"] = drvi()
                        else:
                            print(cmd, msgType, f, t)
                    # message CMsgVector:
                    #  optional float x = 1;
                    #  optional float y = 2;
                    #  optional float z = 3;
                    # optional int32 amount = 1;
                    # optional .CMsgVector inflictor_world_pos = 2;
                    # optional int32 victim_entindex = 3;
                elif msgType == 25:  # CS_UM_ProcessSpottedEntityUpdate
                    parsed["type"] = "CS_UM_ProcessSpottedEntityUpdate"
                    # message SpottedEntityUpdate:
                    #  optional int32 entity_idx = 1;
                    #  optional int32 class_id = 2;
                    #  optional int32 origin_x = 3;
                    #  optional int32 origin_y = 4;
                    #  optional int32 origin_z = 5;
                    #  optional int32 angle_y = 6;
                    #  optional bool defuser = 7;
                    #  optional bool player_has_defuser = 8;
                    #  optional bool player_has_c4 = 9;
                    # optional bool new_update = 1;
                    # repeated SpottedEntityUpdate entity_updates = 2;
                elif msgType == 26:  # CS_UM_ReloadEffect
                    parsed["type"] = "CS_UM_ReloadEffect"
                    # optional int32 entidx = 1;
                    # optional int32 actanim = 2;
                    # optional float origin_x = 3;
                    # optional float origin_y = 4;
                    # optional float origin_z = 5;
                elif msgType == 36:  # CS_UM_PlayerStatsUpdate
                    parsed["type"] = "CS_UM_PlayerStatsUpdate"
                    parsed["stats"] = []
                    for f, t in msgData:
                        if f == 1:
                            parsed["version"] = drvi()
                        elif f == 4:
                            _ = drvi()
                            stat = []
                            for f2, t2 in msgData:
                                if 1 <= f2 <= 2:
                                    stat.append(drvi())
                                elif 4 <= f <= 6:
                                    msgData.undo(1)
                                    break
                                else:
                                    print("", cmd, msgType, f2, t2)
                            parsed["stats"].append(stat)
                        elif f == 5:
                            parsed["user_id"] = drvi()
                        elif f == 6:
                            parsed["crc"] = drvi()
                        else:
                            print(cmd, msgType, f, t)
                    # message Stat:
                    #  optional int32 idx = 1;
                    #  optional int32 delta = 2;
                    # optional int32 version = 1;
                    # repeated .CCSUsrMsg_PlayerStatsUpdate.Stat stats = 4;
                    # optional int32 user_id = 5;
                    # optional int32 crc = 6;
                else:
                    print(cmd, msgType)
                continue
            elif cmd == 25:  # svc_GameEvent
                continue
                event["type"] = "svc_GameEvent"
                event["keys"] = []
                for f, t in message:
                    if f == 1:
                        event["event_name"] = decode(mrvb())
                    elif f == 2:
                        event["eventid"] = mrvi()
                    elif f == 3:
                        _ = mrvi()
                        key = OrderedDict()
                        lastIndex = 0
                        for f2, t2 in message:
                            if f2 < lastIndex or (f2 == 3 and t2 != 5):
                                message.undo(1)
                                break
                            elif f2 == 1:
                                key["type"] = mrvi()
                            elif f2 == 2:
                                key["val_string"] = decode(mrvb())
                            elif f2 == 3:
                                key["val_float"] = message.readFloat()
                            elif f2 == 4:
                                key["val_long"] = mrvi()
                            elif f2 == 5:
                                key["val_short"] = mrvi()
                            elif f2 == 6:
                                key["val_byte"] = mrvi()
                            elif f2 == 7:
                                key["val_bool"] = mrvi()
                            elif f2 == 8:
                                key["val_uint64"] = mrvi()
                            elif f2 == 9:
                                key["val_wstring"] = mrvb()
                            else:
                                print("", cmd, f2, t2)
                            lastIndex = f2
                        try:
                            if key["type"] == 50:
                                print("player_death", key, event)
                        except KeyError:
                            pass
                        event["keys"].append(key)
                    elif f == 4:
                        parsed["passthrough"] = drvi()
                    else:
                        print(cmd, f, t)
                # message key_t:
                #  optional int32 type = 1;
                #  optional string val_string = 2;
                #  optional float val_float = 3;
                #  optional int32 val_long = 4;
                #  optional int32 val_short = 5;
                #  optional int32 val_byte = 6;
                #  optional bool val_bool = 7;
                #  optional uint64 val_uint64 = 8;
                #  optional bytes val_wstring = 9;
                # optional string event_name = 1;
                # optional int32 eventid = 2;
                # repeated .CSVCMsg_GameEvent.key_t keys = 3;
                # optional int32 passthrough = 4;
            elif cmd == 26:  # svc_PacketEntities
                continue
            elif cmd == 27:  # svc_TempEntities
                continue
            elif cmd == 28:  # svc_Prefetch
                continue
            elif cmd == 30:  # svc_GameEventList
                continue
                event["type"] = "svc_GameEventList"
                for f, t in message:
                    if f == 1:
                        for ff, tt in message:
                            if ff == 1:
                                eventId = mrvi()
                            elif ff == 1:
                                eventName = decode(mrvb())
                                print(eventName)
                            elif ff == 3:
                                for fff, ttt in message:
                                    if fff == 1:
                                        keyType = mrvi()
                                    elif fff == 2:
                                        keyName = decode(mrvb())
                                    else:
                                        print(cmd, f, ff, fff, t, tt, ttt)
                            else:
                                print(cmd, f, ff, tt)
                    else:
                        print(cmd, f, t)
                raise SystemExit
                continue
                _ = """message CSVCMsg_GameEventList {
                            message key_t {
                                optional int32 type = 1;
                                optional string name = 2;
                            }

                            message descriptor_t {
                                optional int32 eventid = 1;
                                optional string name = 2;
                                repeated .CSVCMsg_GameEventList.key_t keys = 3;
                            }

                            repeated .CSVCMsg_GameEventList.descriptor_t descriptors = 1;"""
            else:
                print("!%d. (%d)" % (self.progress, cmd))
                raise SystemExit
                break
            print("%02d%s (%d)->%s" % (self.progress, "%", cmd, event["type"]))

    def handle_datatables(self):
        self.buffer.skipIbytes()
        return
        chunk = Buffer(self.buffer.readIBytes())
        numTables = chunk.readByte()

    def handle_stringtables(self):
        self.buffer.skipIbytes()
        return
        chunk = Buffer(self.buffer.readIBytes())
        numTables = chunk.readByte()
        for i in range(numTables):
            tableName = chunk.readString()

    def parse(self):
        data = self.buffer
        handlers = {1: self.handle_signon, 2: self.handle_signon,
                    6: self.handle_datatables, 9: self.handle_stringtables}
        while data.canIterate:
            frameType = data.readByte()
            tick = data.readInt32()
            playerSlot = data.readByte()
            if frameType == 3:  # dem_synctick
                continue
            try:
                handlers[frameType]()
                continue
            except KeyError:
                pass
            if frameType == 7:
                print("Ended at tick %d on offset %d" % (tick, data.offset))
                break
            else:
                print("\n- %d; [%d] at tick %d on slot %d" %
                      (data.offset, frameType, tick, playerSlot))


def main():
    t0 = time()
    path = "90_unik-leadores_de_train.dem"
    # path = "ksn-onlyheroes-rov_gaming day-de_train.dem"
    with open(path, "rb") as f:
        data = f.read()
    game = Game(data)
    print("Took %.4f seconds" % (time() - t0))


if __name__ == "__main__":
    main()
