from nbtlib.tag import End, Byte, Short, Int, Long, Float, Double, ByteArray, String, List, Compound, IntArray, LongArray
import nbtlib
from math import ceil, log
import struct

LITEMATIC_VERSION = 5
MC_DATA_VERSION = 1631

class Schematic:

    def __init__(self, width, height, length, name="Unnamed", author="", description=""):
        self.author = author
        self.description = description
        self.name = name
        self.created = 0 #TODO
        self.modified = 0 #TODO
        self.width, self.height, self.length = width, height, length
        self.regions = []
        pass #TODO

    def getblock(self, x, y, z):
        pass #TODO

    def setblock(self, x, y, z, block):
        pass #TODO

    def save(self, fname):
        pass #TODO

    def _tonbt(self, updatetime=True):
        root = Compound()
        root["Version"] = Int(LITEMATIC_VERSION)
        root["MinecraftDataVersion"] = Int(MC_DATA_VERSION)
        meta = Compound()
        enclose = Compound()
        enclose["x"] = Int(self.width)
        enclose["y"] = Int(self.height)
        enclose["z"] = Int(self.length)
        meta["EnclosingSize"] = enclose
        meta["Author"] = String(self.author)
        meta["Description"] = String(self.description)
        meta["Name"] = String(self.name)
        meta["RegionCount"] = len(self.regions)
        meta["TimeCreated"] = Long(self.created)
        meta["TimeModified"] = Long(self.modified)
        meta["TotalBlocks"] = sum([reg.getblockcount() for reg in self.regions]) #TODO Is this right
        meta["TotalVolume"] = sum([reg.getvolume() for reg in self.regions]) #TODO Is this right
        root["Metadata"] = meta
        regs = Compound()
        for reg in self.regions:
            regs[reg.name] = reg._tonbt()
        root["Regions"] = regs

    def fromnbt(nbt):
        meta = nbt["Metadata"]
        width = int(meta["EnclosingSize"]["x"])
        height = int(meta["EnclosingSize"]["y"])
        length = int(meta["EnclosingSize"]["z"])
        author = nbtstr2str(meta["Author"])
        name = nbtstr2str(meta["Name"])
        desc = nbtstr2str(meta["Description"])
        sch = Schematic(width, height, length, name=name, author=author, description=desc)
        sch.created = int(meta["TimeCreated"])
        sch.modified = int(meta["TimeModified"])
        for key, value in nbt["Regions"].items():
            reg = Region.fromnbt(value, name=nbtstr2str(key))
            sch.regions.append(reg)
        #TODO Compare extracted regions count to stored
        return sch

    def load(fname):
        nbt = nbtlib.File.load(fname, True)['']
        return Schematic.fromnbt(nbt)

class Region:

    def __init__(self, x, y, z, width, height, length, name="Unnamed"):
        self.name = name
        self.x, self.y, self.z = x, y, z
        self.width, self.height, self.length = width, height, length
        self.palette = [AIR, ]
        self.blocks = [[[ 0 for k in range(length)] for j in range(height)] for i in range(width)]
        self.entities = []
        self.tileentities = []
        pass #TODO

    def _tonbt(self):
        root = Compound()
        pos = Compound()
        pos["x"] = Int(self.x)
        pos["y"] = Int(self.y)
        pos["z"] = Int(self.z)
        root["Position"] = pos
        size = Compound()
        size["x"] = width
        size["y"] = height
        size["z"] = length
        root["Size"] = size
        plt = List([blk._tonbt() for blk in self.palette])
        root["BlockStatePalette"] = plt
        ents = List([ent._tonbt() for ent in self.entities])
        root["Entities"] = ents
        tilents = List([ent._tonbt for ent in self.tileentities])
        root["TileEntities"] = tilents
        root["PendingBlockTicks"] = List() #TODO How does this work
        root["PendingFluidTicks"] = List()
        root["BlockStates"] = LongArray() #TODO

    def getblock(self, x, y, z):
        return self.palette[ self.blocks[x][y][z] ]

    def setblock(self, x, y, z, block):
        if block in self.palette:
            i = self.palette.index(block)
        else:
            self.palette.append(block)
            i = len(self.palette) - 1
        self.blocks[x][y][z] = i

    def getblockcount(self):
        airind = self.palette.index(AIR)
        c = 0
        for plan in self.blocks:
            for column in plan:
                for block in column:
                    if block != airind:
                        c += 1
        return c

    def getvolume(self):
        return self.width * self.height * self.length
    
    def fromnbt(nbt, name="Unnamed"):
        pos = nbt["Position"]
        x = int(pos["x"])
        y = int(pos["y"])
        z = int(pos["z"])
        size = nbt["Size"]
        width = int(size["x"])
        height = int(size["y"])
        length = int(size["z"])
        reg = Region(x, y, z, width, height, length)
        del reg.palette[0]
        for bnbt in nbt["BlockStatePalette"]:
            block = BlockState.fromnbt(bnbt)
            reg.palette.append(block)
        for enbt in nbt["Entities"]:
            entity = Entity.fromnbt(entity)
            reg.entities.append(entity)
        for tenbt in nbt["TileEntities"]:
            block = TileEntity.fromnbt(tentity)
            reg.tileentities.append(block)
        #TODO Blocks
        blks = nbt["BlockStates"]
        nbits = ceil(log(len(reg.palette))) + 1
        #print(nbits)
        i = 0 # The longs we have consummed
        buff = 0
        buffbits = 0
        for j in range(reg.getvolume()):
            while buffbits < nbits:
                buff <<= 64
                buff += int(struct.unpack('L', struct.pack('L', blks[i])[::-1])[0])
                i += 1
                buffbits += 64
                #print(buff)
            ind = buff >> (buffbits - nbits)
            print(struct.pack('L', buff))
            buff &= (1 << (buffbits - nbits + 1)) - 1
            buffbits -= nbits
            print(ind)
        return reg

class BlockState:

    def __init__(self, blockid):
        self.blockid = blockid
        self.properties = {}

    def _tonbt(self):
        root = Compound()
        root["Name"] = String(self.blockid)
        if len(self.properties) > 0:
            root["Properties"] = Compound(self.properties)
        return root

    def fromnbt(nbt):
        block = BlockState(nbtstr2str(nbt["Name"]))
        for key, value in nbt.items():
            block.properties[nbtstr2str(key)] = nbtstr2str(value)
        return block

class Entity:

    def __init__(self):
        pass #TODO

    def _tonbt(self):
        raise NotImplementedError("Entities are not supported yet")

class TileEntity:

    def __init__(self):
        pass #TODO

    def _tonbt(self):
        raise NotImplementedError("Tile entities are not supported yet")

def nbtstr2str(s):
    return str(s)[1:-1]

AIR = BlockState("minecraft:air")

