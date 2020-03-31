from nbtlib.tag import End, Byte, Short, Int, Long, Float, Double, ByteArray, String, List, Compound, IntArray, LongArray
import nbtlib
from math import ceil, log
from .storage import LitematicaBitArray
from time import time

LITEMATIC_VERSION = 5
MC_DATA_VERSION = 1631
DEFAULT_NAME = "Unnamed" # Default name given to schematics and regions if unspecified

class Schematic:

    def __init__(self, width, height, length, name=DEFAULT_NAME, author="", description=""):
        self.author = author
        self.description = description
        self.name = name
        self.created = int(time())
        self.modified = int(time())
        self.width, self.height, self.length = width, height, length
        self.regions = []

    def save(self, fname):
        f = nbtlib.File(gzipped=True, byteorder='big')
        f[""] = self._tonbt()
        f.save(fname)

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
        meta["RegionCount"] = Int(len(self.regions))
        meta["TimeCreated"] = Long(self.created)
        meta["TimeModified"] = Long(self.modified)
        meta["TotalBlocks"] = Int(sum([reg.getblockcount() for reg in self.regions])) 
        meta["TotalVolume"] = Int(sum([reg.getvolume() for reg in self.regions]))
        root["Metadata"] = meta
        regs = Compound()
        for reg in self.regions:
            regs[reg.name] = reg._tonbt()
        root["Regions"] = regs
        return root

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
        if "RegionCount" in meta and len(sch.regions) != meta["RegionCount"]:
            raise CorruptedSchematicError("Number of regions in metadata does not match the number of parsed regions")
        return sch

    def load(fname):
        nbt = nbtlib.File.load(fname, True)['']
        return Schematic.fromnbt(nbt)

class Region:

    def __init__(self, x, y, z, width, height, length, name=DEFAULT_NAME):
        self.name = name
        self.x, self.y, self.z = x, y, z
        self.width, self.height, self.length = width, height, length
        self.palette = [AIR, ]
        self.blocks = [[[ 0 for k in range(abs(length))] for j in range(abs(height))] for i in range(abs(width))]
        self.entities = []
        self.tileentities = []

    def _tonbt(self):
        root = Compound()
        pos = Compound()
        pos["x"] = Int(self.x)
        pos["y"] = Int(self.y)
        pos["z"] = Int(self.z)
        root["Position"] = pos
        size = Compound()
        size["x"] = Int(self.width)
        size["y"] = Int(self.height)
        size["z"] = Int(self.length)
        root["Size"] = size
        plt = List[Compound]([blk._tonbt() for blk in self.palette])
        root["BlockStatePalette"] = plt
        ents = List[Compound]([ent._tonbt() for ent in self.entities])
        root["Entities"] = ents
        tilents = List[Compound]([ent._tonbt for ent in self.tileentities])
        root["TileEntities"] = tilents
        root["PendingBlockTicks"] = List[Compound]() #TODO How does this work
        root["PendingFluidTicks"] = List[Compound]()
        arr = LitematicaBitArray(self.getvolume(), self.__get_needed_nbits())
        for x in range(abs(self.width)):
            for y in range(abs(self.height)):
                for z in range(abs(self.length)):
                    ind = (y * abs(self.width * self.length)) + z * abs(self.width) + x
                    arr[ind] = self.blocks[x][y][z]
        root["BlockStates"] = arr._tonbtlongarray()
        return root

    def getblock(self, x, y, z):
        if self.width < 0:
            x -= self.width + 1
        if self.height < 0:
            y -= self.height + 1
        if self.length < 0:
            z -= self.length + 1
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
        return abs(self.width * self.height * self.length)

    def __get_needed_nbits(self):
        return max(ceil(log(len(self.palette), 2)), 2)
    
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
        blks = nbt["BlockStates"]
        nbits = reg.__get_needed_nbits()
        arr = LitematicaBitArray.fromnbtlongarray(blks, reg.getvolume(), nbits)
        for x in range(abs(width)):
            for y in range(abs(height)):
                for z in range(abs(length)):
                    ind = (y * abs(width * length)) + z * abs(width) + x
                    reg.blocks[x][y][z] = arr[ind]
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

class CorruptedSchematicError(Exception):
    pass

