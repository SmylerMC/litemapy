from nbtlib.tag import End, Byte, Short, Int, Long, Float, Double, ByteArray, String, List, Compound, IntArray, LongArray
import nbtlib
from math import ceil, log
from .storage import LitematicaBitArray, DiscriminatingDictionnary
from .info import *
from .boxes import *
from time import time

class Schematic:

    """
    A schematic file
    """

    def __init__(self,
                    width, height, length, 
                    name=DEFAULT_NAME, author="", description="",
                    regions={}, main_region_name=DEFAULT_NAME
                ):
        """
        Initialize a schematic of size width, height and length
        name, author and description are used in metadatas
        regions should be disctionnary {'regionname': region} to add to the schematic
        If region is None or empty, an empty region, named after main_region_name,
        and of the size of the schematic is created at its origin
        """
        self.author = author
        self.description = description
        self.name = name
        self.created = int(time())
        self.modified = int(time())
        self.__width, self.__height, self.__length = width, height, length
        self.__regions = DiscriminatingDictionnary(self._can_add_region)
        if regions != None and len(regions) > 0:
            self.__regions.update(regions)
        else:
            reg = Region(0, 0, 0, self.width, self.height, self.length)
            self.__regions[main_region_name] = reg

    def save(self, fname, update_meta=True, save_soft=True):
        """
        Save this schematic to the disk in a file name fname
        update_meta: update metadata before writing to the disk (modified time)
        save_soft: add a metadata entry with the software name and version
        """
        if update_meta:
            self.updatemeta()
        f = nbtlib.File(gzipped=True, byteorder='big')
        f[""] = self._tonbt(save_soft=save_soft)
        f.save(fname)

    def _tonbt(self, save_soft=True):
        """
        Write the schematic to an nbt tag
        """
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
        meta["Software"] = String(LITEMAPY_NAME + "_" + LITEMAPY_VERSION)
        meta["RegionCount"] = Int(len(self.regions))
        meta["TimeCreated"] = Long(self.created)
        meta["TimeModified"] = Long(self.modified)
        meta["TotalBlocks"] = Int(sum([reg.getblockcount() for reg in self.regions.values()])) 
        meta["TotalVolume"] = Int(sum([reg.getvolume() for reg in self.regions.values()]))
        root["Metadata"] = meta
        regs = Compound()
        for regname, reg in self.regions.items():
            regs[regname] = reg._tonbt()
        root["Regions"] = regs
        return root

    def fromnbt(nbt):
        """
        Read and return a schematic from an nbt tag
        """
        meta = nbt["Metadata"]
        width = int(meta["EnclosingSize"]["x"])
        height = int(meta["EnclosingSize"]["y"])
        length = int(meta["EnclosingSize"]["z"])
        author = nbtstr2str(meta["Author"])
        name = nbtstr2str(meta["Name"])
        desc = nbtstr2str(meta["Description"])
        regions = {}
        for key, value in nbt["Regions"].items():
            reg = Region.fromnbt(value)
            regions[str(key)] = reg
        sch = Schematic(width, height, length, name=name, author=author, description=desc, regions=regions)
        sch.created = int(meta["TimeCreated"])
        sch.modified = int(meta["TimeModified"])
        if "RegionCount" in meta and len(sch.regions) != meta["RegionCount"]:
            raise CorruptedSchematicError("Number of regions in metadata does not match the number of parsed regions")
        return sch

    def updatemeta(self):
        """
        Update this schematic's metadata (modified time)
        """
        self.modified = int(time())

    def load(fname):
        """
        Read a schematic from disk
        fname; nale of the file
        """
        nbt = nbtlib.File.load(fname, True)['']
        return Schematic.fromnbt(nbt)

    def _can_add_region(self, name, region):
        if type(name) != str:
            return False, "Region name should be a string"
        schembox = ((0, 0, 0), (self.width-1, self.height-1, self.length-1))
        regx, regy, regz = region.x, region.y, region.z
        regbx = regx + region.width - abs(region.width) / region.width
        regby = regy + region.height - abs(region.height) / region.height
        regbz = regz + region.length - abs(region.length) / region.length
        regbox = ((regx, regy, regz), (regbx, regy, regz))
        if not box_is_in_box(regbox, schembox):
            return False, "The region does not fit in the schematic"
        return True, ""

    @property
    def regions(self):
        return self.__regions
    
    @property
    def width(self):
        return self.__width

    @property
    def height(self):
        return self.__height

    @property
    def length(self):
        return self.__length

class Region:

    """
    A schematic region
    x, y, z: position in the schematic (read only)
    width, height, length: size of the region (oriented, can be negative)
    """

    def __init__(self, x, y, z, width, height, length):
        self.__x, self.__y, self.__z = x, y, z
        self.__width, self.__height, self.__length = width, height, length
        self.__palette = [AIR, ]
        self.__blocks = [[[ 0 for k in range(abs(length))] for j in range(abs(height))] for i in range(abs(width))]
        self.entities = [] #TODO Add support
        self.tileentities = [] #TODO Add support

    def _tonbt(self):
        """
        Write this region to an nbt tab and return it
        """
        root = Compound()
        pos = Compound()
        pos["x"] = Int(self.__x)
        pos["y"] = Int(self.__y)
        pos["z"] = Int(self.__z)
        root["Position"] = pos
        size = Compound()
        size["x"] = Int(self.__width)
        size["y"] = Int(self.__height)
        size["z"] = Int(self.__length)
        root["Size"] = size
        plt = List[Compound]([blk._tonbt() for blk in self.__palette])
        root["BlockStatePalette"] = plt
        ents = List[Compound]([ent._tonbt() for ent in self.entities])
        root["Entities"] = ents
        tilents = List[Compound]([ent._tonbt for ent in self.tileentities])
        root["TileEntities"] = tilents
        root["PendingBlockTicks"] = List[Compound]() #TODO How does this work
        root["PendingFluidTicks"] = List[Compound]()
        arr = LitematicaBitArray(self.getvolume(), self.__get_needed_nbits())
        for x in range(abs(self.__width)):
            for y in range(abs(self.__height)):
                for z in range(abs(self.__length)):
                    ind = (y * abs(self.__width * self.__length)) + z * abs(self.__width) + x
                    arr[ind] = self.__blocks[x][y][z]
        root["BlockStates"] = arr._tonbtlongarray()
        return root

    def getblock(self, x, y, z):
        """
        Return the block at the given coordinates
        """
        if self.__width < 0:
            x -= self.__width + 1
        if self.__height < 0:
            y -= self.__height + 1
        if self.__length < 0:
            z -= __self.length + 1
        return self.__palette[ self.__blocks[x][y][z] ]

    def setblock(self, x, y, z, block):
        """
        Set the block at the given coordinate
        """
        if block in self.__palette:
            i = self.__palette.index(block)
        else:
            self.__palette.append(block)
            i = len(self.__palette) - 1
        self.__blocks[x][y][z] = i

    def getblockcount(self):
        """
        Returns the number of non-air in the region
        """
        airind = self.__palette.index(AIR)
        c = 0
        for plan in self.__blocks:
            for column in plan:
                for block in column:
                    if block != airind:
                        c += 1
        return c

    def getvolume(self):
        """
        Returns the region's volume
        """
        return abs(self.__width * self.__height * self.__length)

    def __get_needed_nbits(self):
        return max(ceil(log(len(self.__palette), 2)), 2)
    
    def fromnbt(nbt):
        """
        Read a region from an nbt tag and return it
        """
        pos = nbt["Position"]
        x = int(pos["x"])
        y = int(pos["y"])
        z = int(pos["z"])
        size = nbt["Size"]
        width = int(size["x"])
        height = int(size["y"])
        length = int(size["z"])
        reg = Region(x, y, z, width, height, length)
        del reg.__palette[0]
        for bnbt in nbt["BlockStatePalette"]:
            block = BlockState.fromnbt(bnbt)
            reg.__palette.append(block)
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
                    reg.__blocks[x][y][z] = arr[ind]
        return reg

    @property
    def x(self):
        return self.__x

    @property
    def y(self):
        return self.__y

    @property
    def z(self):
        return self.__z

    @property
    def width(self):
        return self.__width

    @property
    def height(self):
        return self.__height

    @property
    def length(self):
        return self.__length



class BlockState:

    def __init__(self, blockid, properties={}):
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

