from json import dumps
from math import ceil, log
from time import time

import nbtlib
import numpy as np
from nbtlib.tag import Int, Long, Double, String, List, Compound, IntArray

from .info import *
from .storage import LitematicaBitArray, DiscriminatingDictionary


class Schematic:
    """
    A schematic file
    """

    def __init__(self,
                    name=DEFAULT_NAME, author="", description="",
                    regions={}, lm_version=LITEMATIC_VERSION, mc_version=MC_DATA_VERSION
                ):
        """
        Initialize a schematic of size width, height and length
        name, author and description are used in metadata
        regions should be dictionary {'regionname': region} to add to the schematic
        """
        self.author = author
        self.description = description
        self.name = name
        self.created = round(time() * 1000)
        self.modified = round(time() * 1000)
        self.__regions = DiscriminatingDictionary(self._can_add_region,
                                                  onadd=self.__on_region_add, onremove=self.__on_region_remove)
        self.__compute_enclosure()
        if regions is not None and len(regions) > 0:
            self.__regions.update(regions)
        self.mc_version = mc_version
        self.lm_version = lm_version
        self.__preview = IntArray([])

    def save(self, fname, update_meta=True, save_soft=True, gzipped=True, byteorder='big'):
        """
        Save this schematic to the disk in a file name fname
        update_meta: update metadata before writing to the disk (modified time)
        save_soft: add a metadata entry with the software name and version
        """
        if update_meta:
            self.updatemeta()
        f = nbtlib.File(self._tonbt(save_soft=save_soft), gzipped=gzipped, byteorder=byteorder)
        f.save(fname)

    def _tonbt(self, save_soft=True):
        """
        Write the schematic to an nbt tag.
        Raises ValueError if this schematic has no region.
        """
        if len(self.__regions) < 1:
            raise ValueError("Empty schematic does not have any regions")
        root = Compound()
        root["Version"] = Int(self.lm_version)
        root["MinecraftDataVersion"] = Int(self.mc_version)
        meta = Compound()
        enclose = Compound()
        enclose["x"] = Int(self.width)
        enclose["y"] = Int(self.height)
        enclose["z"] = Int(self.length)
        meta["EnclosingSize"] = enclose
        meta["Author"] = String(self.author)
        meta["Description"] = String(self.description)
        meta["Name"] = String(self.name)
        if save_soft:
            meta["Software"] = String(LITEMAPY_NAME + "_" + LITEMAPY_VERSION)
        meta["RegionCount"] = Int(len(self.regions))
        meta["TimeCreated"] = Long(self.created)
        meta["TimeModified"] = Long(self.modified)
        meta["TotalBlocks"] = Int(sum([reg.getblockcount() for reg in self.regions.values()]))
        meta["TotalVolume"] = Int(sum([reg.getvolume() for reg in self.regions.values()]))
        meta['PreviewImageData'] = self.__preview
        root["Metadata"] = meta
        regs = Compound()
        for regname, reg in self.regions.items():
            regs[regname] = reg._tonbt()
        root["Regions"] = regs
        return root

    @staticmethod
    def fromnbt(nbt):
        """
        Read and return a schematic from an nbt tag
        """
        meta = nbt["Metadata"]
        lm_version = nbt["Version"]
        mc_version = nbt["MinecraftDataVersion"]
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
        sch = Schematic(name=name, author=author, description=desc, regions=regions, lm_version=lm_version, mc_version=mc_version)
        if sch.width != width:
            raise CorruptedSchematicError("Invalid schematic width in metadata, excepted {} was {}".format(sch.width, width))
        if sch.height != height:
            raise CorruptedSchematicError(
                "Invalid schematic height in metadata, excepted {} was {}".format(sch.height, height))
        if sch.length != length:
            raise CorruptedSchematicError(
                "Invalid schematic length in metadata, excepted {} was {}".format(sch.length, length))
        sch.created = int(meta["TimeCreated"])
        sch.modified = int(meta["TimeModified"])
        if "RegionCount" in meta and len(sch.regions) != meta["RegionCount"]:
            raise CorruptedSchematicError("Number of regions in metadata does not match the number of parsed regions")
        if 'PreviewImageData' in meta.keys():
            sch.__preview = meta['PreviewImageData']
        return sch

    def updatemeta(self):
        """
        Update this schematic's metadata (modified time)
        """
        self.modified = round(time() * 1000)

    @staticmethod
    def load(fname):
        """
        Read a schematic from disk
        fname: name of the file
        """
        nbt = nbtlib.File.load(fname, True)
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

    @property
    def preview(self):
        return self.__preview

    @preview.setter
    def preview(self, value):
        self.__preview = value


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
        self.entities = []
        self.tile_entities = []
        self.blockTicks = []
        self.fluidTicks = []

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

        entities = List[Compound]([entity._tonbt() for entity in self.entities])
        root["Entities"] = entities

        tile_entities = List[Compound]([tile_entity._tonbt() for tile_entity in self.tile_entities])
        root["TileEntities"] = tile_entities

        root["PendingBlockTicks"] = List[Compound](self.blockTicks) #TODO How does this work
        root["PendingFluidTicks"] = List[Compound](self.fluidTicks)

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

    @staticmethod
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

        for entity_nbt in nbt["Entities"]:
            entity = Entity.fromnbt(entity_nbt)
            reg.entities.append(entity)

        for tile_entity_nbt in nbt["TileEntities"]:
            block = TileEntity.fromnbt(tile_entity_nbt)
            reg.tile_entities.append(block)

        blks = nbt["BlockStates"]
        nbits = reg.__get_needed_nbits()
        arr = LitematicaBitArray.fromnbtlongarray(blks, reg.getvolume(), nbits)
        for x in range(abs(width)):
            for y in range(abs(height)):
                for z in range(abs(length)):
                    ind = (y * abs(width * length)) + z * abs(width) + x
                    reg.__blocks[x][y][z] = arr[ind]

        for blockTick in nbt["PendingBlockTicks"]:
            reg.blockTicks.append(blockTick)

        for fluidTick in nbt["PendingFluidTicks"]:
            reg.fluidTicks.append(fluidTick)

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
        self.__properties = DiscriminatingDictionary(self.__validate, properties)

    def _tonbt(self):
        root = Compound()
        root["Name"] = String(self.blockid)
        properties = {String(k): String(v) for k, v in self.__properties.items()}
        if len(properties) > 0:
            root["Properties"] = Compound(properties)
        return root

    @staticmethod
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
            return False, "Blockstate properties should be a string => string dictionary"
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

    def __init__(self, str_or_nbt):

        if isinstance(str_or_nbt, str):
            self._data = Compound({'id': String(str_or_nbt)})
        else:
            self._data = str_or_nbt

        keys = self._data.keys()
        if 'id' not in keys:
            raise RequiredKeyMissingException('id')
        if 'Pos' not in keys:
            self._data['Pos'] = List[Double]([Double(0.), Double(0.), Double(0.)])
        if 'Rotation' not in keys:
            self._data['Rotation'] = List[Double]([Double(0.), Double(0.)])
        if 'Motion' not in keys:
            self._data['Motion'] = List[Double]([Double(0.), Double(0.), Double(0.)])

        self._id = self._data['id']
        self._position = tuple([float(coord) for coord in self._data['Pos']])
        self._rotation = tuple([float(coord) for coord in self._data['Rotation']])
        self._motion = tuple([float(coord) for coord in self._data['Motion']])

    def _tonbt(self):
        return self._data

    @staticmethod
    def fromnbt(nbt):
        return Entity(nbt)

    def add_tag(self, key, tag):
        self._data[key] = tag
        if key == 'id':
            self._id = str(tag)
        if key == 'Pos':
            self._position = (float(coord) for coord in tag)
        if key == 'Rotation':
            self._rotation = (float(coord) for coord in tag)
        if key == 'Motion':
            self._motion = (float(coord) for coord in tag)

    def get_tag(self, key):
        try:
            return self._data[key]
        except KeyError:
            raise

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = Entity(data).data
        self._id = str(self._data['id'])
        self._position = tuple([float(coord) for coord in self._data['Pos']])
        self._rotation = tuple([float(coord) for coord in self._data['Rotation']])
        self._motion = tuple([float(coord) for coord in self._data['Motion']])

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        self._id = id
        self._data['id'] = String(self._id)

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, position):
        self._position = position
        self._data['Pos'] = List[Double]([Double(coord) for coord in self._position])

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, rotation):
        self._rotation = rotation
        self._data['Rotation'] = List[Double]([Double(coord) for coord in self._rotation])

    @property
    def motion(self):
        return self._motion

    @motion.setter
    def motion(self, motion):
        self._motion = motion
        self._data['Motion'] = List[Double]([Double(coord) for coord in self._motion])


class TileEntity:

    def __init__(self, str_or_nbt):

        if isinstance(str_or_nbt, str):
            self._data = Compound({'id': String(str_or_nbt)})
        else:
            self._data = str_or_nbt

        keys = self._data.keys()
        if 'id' not in keys:
            raise RequiredKeyMissingException('id')
        if 'x' not in keys:
            self._data['x'] = Int(0)
        if 'y' not in keys:
            self._data['y'] = Int(0)
        if 'z' not in keys:
            self._data['z'] = Int(0)

        self._id = self._data['id']
        self._position = tuple([int(self._data[coord]) for coord in ['x', 'y', 'z']])

    def _tonbt(self):
        return self._data

    @staticmethod
    def fromnbt(nbt):
        return TileEntity(nbt)

    def add_tag(self, key, tag):
        self._data[key] = tag
        if key == 'id':
            self._id = str(tag)

        pos = self._position
        if key == 'x':
            self._position = (int(tag), pos[1], pos[2])
        if key == 'y':
            self._position = (pos[0], int(tag), pos[2])
        if key == 'z':
            self._position = (pos[0], pos[1], int(tag))

    def get_tag(self, key):
        try:
            return self._data[key]
        except KeyError:
            raise

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = TileEntity(data).data
        self._id = str(self._data['id'])
        self._position = tuple([int(self._data[coord]) for coord in ['x', 'y', 'z']])

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        self._id = id
        self._data['id'] = String(self._id)

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, position):
        self._position = position
        for coord, index in [('x', 0), ('y', 1), ('z', 2)]:
            self._data[coord] = Int(self._position[index])


AIR = BlockState("minecraft:air")


class CorruptedSchematicError(Exception):
    pass


class RequiredKeyMissingException(Exception):

    def __init__(self, key, message='The required key is missing in the (Tile)Entity\'s NBT Compound'):
        self.key = key
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.key} -> {self.message}'
