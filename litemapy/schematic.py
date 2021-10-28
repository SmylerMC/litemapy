from nbtlib.tag import End, Byte, Short, Int, Long, Float, Double, ByteArray, String, List, Compound, IntArray, LongArray
import nbtlib
from math import ceil, log
from .storage import LitematicaBitArray, DiscriminatingDictionnary
from .info import *
from .boxes import *
from time import time
import numpy as np
from json import dumps

class Schematic:

    """
    A schematic file
    """

    def __init__(self, 
                    name=DEFAULT_NAME, author="", description="",
                    regions={}
                ):
        """
        Initialize a schematic of size width, height and length
        name, author and description are used in metadatas
        regions should be disctionnary {'regionname': region} to add to the schematic
        """
        self.author = author
        self.description = description
        self.name = name
        self.created = round(time() * 1000)
        self.modified = round(time() * 1000)
        self.__regions = DiscriminatingDictionnary(self._can_add_region, onadd=self.__on_region_add, onremove=self.__on_region_remove)
        self.__compute_enclosure()
        if regions is not None and len(regions) > 0:
            self.__regions.update(regions)

    def save(self, fname, update_meta=True, save_soft=True):
        """
        Save this schematic to the disk in a file name fname
        update_meta: update metadata before writing to the disk (modified time)
        save_soft: add a metadata entry with the software name and version
        """
        if update_meta:
            self.updatemeta()
        f = nbtlib.File(self._tonbt(save_soft=save_soft), gzipped=True, byteorder='big')
        f.save(fname)

    def _tonbt(self, save_soft=True):
        """
        Write the schematic to an nbt tag.
        Raises ValueError if this schematic has no region.
        """
        if len(self.__regions) < 1:
            raise ValueError("Empty schematic does not have y region")
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
        author = str(meta["Author"])
        name = str(meta["Name"])
        desc = str(meta["Description"])
        regions = {}
        for key, value in nbt["Regions"].items():
            reg = Region.fromnbt(value)
            regions[str(key)] = reg
        sch = Schematic(name=name, author=author, description=desc, regions=regions)
        if sch.width != width:
            raise CorruptedSchematicError("Invalid schematic width in metadata, excepted {} was {}".format(sch.width, width))
        if sch.height != height:
            raise CorruptedSchematicError("Invalid schematic height in metadata, excepted {} was {}".format(sch.height, height))
        if sch.length != length:
            raise CorruptedSchematicError("Invalid schematic length in metadata, excepted {} was {}".format(sch.length, length))
        sch.created = int(meta["TimeCreated"])
        sch.modified = int(meta["TimeModified"])
        if "RegionCount" in meta and len(sch.regions) != meta["RegionCount"]:
            raise CorruptedSchematicError("Number of regions in metadata does not match the number of parsed regions")
        return sch

    def updatemeta(self):
        """
        Update this schematic's metadata (modified time)
        """
        self.modified = round(time() * 1000)

    def load(fname):
        """
        Read a schematic from disk
        fname: name of the file
        """
        nbt = nbtlib.File.load(fname, True)
        print(nbt)
        return Schematic.fromnbt(nbt)

    def _can_add_region(self, name, region):
        if type(name) != str:
            return False, "Region name should be a string"
        return True, ""

    def __on_region_add(self, name, region):
        if self.__xmin is None:
            self.__xmin = region.minschemx()
        else:
            self.__xmin = min(self.__xmin, region.minschemx())
        if self.__xmax is None:
            self.__xmax = region.maxschemx()
        else:
            self.__xmax = max(self.__xmax, region.maxschemx())
        if self.__ymin is None:
            self.__ymin = region.minschemy()
        else:
            self.__ymin = min(self.__ymin, region.minschemy())
        if self.__ymax is None:
            self.__ymax = region.maxschemy()
        else:
            self.__ymax = max(self.__ymax, region.maxschemy())
        if self.__zmin is None:
            self.__zmin = region.minschemz()
        else:
            self.__zmin = min(self.__zmin, region.minschemz())
        if self.__zmax is None:
            self.__zmax = region.maxschemz()
        else:
            self.__zmax = max(self.__zmax, region.maxschemz())

    def __on_region_remove(self, name, region):
        b = self.__xmin == region.minschemx()
        b = b or self.__xmax == region.maxschemx()
        b = b or self.__ymin == region.minschemy()
        b = b or self.__ymax == region.maxschemy()
        b = b or self.__zmin == region.minschemz()
        b = b or self.__zmax == region.maxschemz()
        if b:
            self.__compute_enclosure()

    def __compute_enclosure(self):
        xmi, xma, ymi, yma, zmi, zma = None, None, None, None, None, None
        for region in self.__regions.values():
            xmi = min(xmi, region.minschemx()) if xmi is not None else region.minschemx()
            xma = max(xma, region.maxschemx()) if xma is not None else region.maxschemx()
            ymi = min(ymi, region.minschemy()) if ymi is not None else region.minschemy()
            yma = max(yma, region.maxschemy()) if yma is not None else region.maxschemy()
            zmi = min(zmi, region.minschemz()) if zmi is not None else region.minschemz()
            zma = max(zma, region.maxschemz()) if zma is not None else region.maxschemz()
        self.__xmin = xmi
        self.__xmax = xma
        self.__ymin = ymi
        self.__ymax = yma
        self.__zmin = zmi
        self.__zmax = zma

    @property
    def regions(self):
        return self.__regions
    
    @property
    def width(self):
        if self.__xmin is None or self.__xmax is None:
            return 0
        return self.__xmax - self.__xmin + 1

    @property
    def height(self):
        if self.__ymin is None or self.__ymax is None:
            return 0
        return self.__ymax - self.__ymin + 1

    @property
    def length(self):
        if self.__zmin is None or self.__zmax is None:
            return 0
        return self.__zmax - self.__zmin + 1

class Region:

    """
    A schematic region
    x, y, z: position in the schematic (read only)
    width, height, length: size of the region (oriented, can be negative)
    """

    def __init__(self, x, y, z, width, height, length):
        if width == 0 or height == 0 or length == 0:
            raise ValueError("Region dimensions cannot be 0")
        self.__x, self.__y, self.__z = x, y, z
        self.__width, self.__height, self.__length = width, height, length
        self.__palette = [AIR, ]
        self.__blocks = np.zeros((abs(width), abs(height), abs(length)), dtype=np.uint32)
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
                    arr[ind] = int(self.__blocks[x, y, z])
        root["BlockStates"] = arr._tonbtlongarray()
        return root

    def getblock(self, x, y, z):
        """
        Return the block at the given coordinates
        """
        x, y, z = self.__regcoordinates2storecoords(x, y, z)
        return self.__palette[self.__blocks[x, y, z]]

    def setblock(self, x, y, z, block):
        """
        Set the block at the given coordinate
        """
        x, y, z = self.__regcoordinates2storecoords(x, y, z)
        if block in self.__palette:
            i = self.__palette.index(block)
        else:
            self.__palette.append(block)
            i = len(self.__palette) - 1
        self.__blocks[x, y, z] = i

    def getblockcount(self):
        """
        Returns the number of non-air in the region
        """
        airind = self.__palette.index(AIR)
        c = 0
        for block in self.__blocks.flat:
            if block != airind:
                c += 1
        return c

    def __regcoordinates2storecoords(self, x, y, z):
        if self.__width < 0:
            x -= self.__width + 1
        if self.__height < 0:
            y -= self.__height + 1
        if self.__length < 0:
            z -= self.__length + 1
        return x, y, z


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

    def minschemx(self):
        """
        Returns the minimum X coordinate of this region in the schematics coordinate system
        """
        return min(self.__x, self.__x + self.width + 1)

    def maxschemx(self):
        """
        Returns the maximum X coordinate of this region in the schematics coordinate system
        """
        return max(self.__x, self.__x + self.width - 1)

    def minschemy(self):
        """
        Returns the minimum Y coordinate of this region in the schematics coordinate system
        """
        return min(self.__y, self.__y + self.height + 1)

    def maxschemy(self):
        """
        Returns the maximum Y coordinate of this region in the schematics coordinate system
        """
        return max(self.__y, self.__y + self.height - 1)

    def minschemz(self):
        """
        Returns the minimum Z coordinate of this region in the schematics coordinate system
        """
        return min(self.__z, self.__z + self.length + 1)

    def maxschemz(self):
        """
        Returns the maximum Z coordinate of this region in the schematics coordinate system
        """
        return max(self.__z, self.__z + self.length - 1)

    def minx(self):
        """
        Returns the minimum X coordinate of this region in its own coordinate system
        """
        return min(0, self.width + 1)

    def maxx(self):
        """
        Returns the maximum X coordinate of this region in its own coordinate system
        """
        return max(0, self.width - 1)

    def miny(self):
        """
        Returns the minimum Y coordinate of this region in its own coordinate system
        """
        return min(0, self.height + 1)

    def maxy(self):
        """
        Returns the maximum Y coordinate of this region in its own coordinate system
        """
        return max(0, self.height - 1)

    def minz(self):
        """
        Returns the minimum Z coordinate of this region in its own coordinate system
        """
        return min(0, self.length + 1)

    def maxz(self):
        """
        Returns the maximum Z coordinate of this region in its own coordinate system
        """
        return max(0, self.length - 1)

    def xrange(self):
        """
        Returns the range of coordinates this region contains along it's X axis
        """
        return range(self.minx(), self.maxx() + 1)

    def yrange(self):
        """
        Returns the range of coordinates this region contains along it's Y axis
        """
        return range(self.miny(), self.maxy() + 1)

    def zrange(self):
        """
        Returns the range of coordinates this region contains along it's Z axis
        """
        return range(self.minz(), self.maxz() + 1)

    def allblockpos(self):
        """
        Returns an iterator over the coordinates this regions contains in its own coordinate system
        """
        for x in self.xrange():
            for y in self.yrange():
                for z in self.zrange():
                    yield x, y, z
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

    def as_schematic(self, name=DEFAULT_NAME, author="", description=""):
        """
        Creates and returns a schematic that contains that region at the origin.
        name: A name for both the region and the schematic
        author: an author for the schematic
        description: a description for the schematic
        """
        return Schematic(name=name, author=author, description=description, regions={name: self})

class BlockState:

    def __init__(self, blockid, properties={}):
        self.__blockid = blockid
        self.__properties = DiscriminatingDictionnary(self.__validate, properties)

    def _tonbt(self):
        root = Compound()
        root["Name"] = String(self.blockid)
        properties = {String(k): String(v) for k, v in self.__properties.items()}
        if len(properties) > 0:
            root["Properties"] = Compound(properties)
        return root

    def fromnbt(nbt):
        bid = str(nbt["Name"])
        if "Properties" in nbt:
            properties = {str(k): str(v) for k, v in nbt["Properties"].items()}
        else:
            properties = {}
        block = BlockState(bid, properties=properties)
        return block

    @property
    def blockid(self):
        return self.__blockid

    def __validate(self, k, v):
        if type(k) is not str or type(v) is not str:
            return False, "Blockstate properties should be a string => string dictionnary"
        return True, ""

    def __eq__(self, other):
        if not isinstance(other, BlockState):
            raise ValueError("Can only compare blockstates with blockstates")
        return other.__blockid == self.__blockid and other.__properties == self.__properties

    def __repr__(self):
        return self.__blockid + dumps(self.__properties)

    def __getitem__(self, key):
        return self.__properties[key]
    
    def __len__(self):
        return len(self.__properties)

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

AIR = BlockState("minecraft:air")

class CorruptedSchematicError(Exception):
    pass

