from json import dumps
from math import ceil, log
from time import time

import nbtlib
import numpy as np
from nbtlib.tag import Short, Byte, Int, Long, Double, String, List, Compound, ByteArray, IntArray

from .info import *
from .Storage import LitematicaBitArray, DiscriminatingDictionary
from .Exception import CorruptedSchematicError, RequiredKeyMissingException

from .BlockState import BlockState
from .Entity import Entity
from .TileEntity import TileEntity



AIR = BlockState("minecraft:air")





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
        self.__entities = []
        self.__tile_entities = []
        self.__block_ticks = []
        self.__fluid_ticks = []

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

        entities = List[Compound]([entity._tonbt() for entity in self.__entities])
        root["Entities"] = entities

        tile_entities = List[Compound]([tile_entity._tonbt() for tile_entity in self.__tile_entities])
        root["TileEntities"] = tile_entities

        root["PendingBlockTicks"] = List[Compound](self.__block_ticks)
        root["PendingFluidTicks"] = List[Compound](self.__fluid_ticks)

        arr = LitematicaBitArray(self.getvolume(), self.__get_needed_nbits())
        for x in range(abs(self.__width)):
            for y in range(abs(self.__height)):
                for z in range(abs(self.__length)):
                    ind = (y * abs(self.__width * self.__length)) + z * abs(self.__width) + x
                    arr[ind] = int(self.__blocks[x, y, z])
        root["BlockStates"] = arr._tonbtlongarray()

        return root

    def to_sponge_nbt(self, mc_version=MC_DATA_VERSION, gzipped=True, byteorder='big'):
        """
        Returns the Region as an NBT Compound file that conforms to the Sponge Schematic Format (version 2) used by mods
        like WorldEdit (https://github.com/SpongePowered/Schematic-Specification).

        Parameters
        ----------
        mc_version : int, default=info.MC_DATA_VERSION
            Minecraft data version that is being emulated (https://minecraft.fandom.com/wiki/Data_version). Should not
            be critical for newer versions of Minecraft.
        gzipped : bool, default=True
            Whether the NBT Compound file should be compressed (WorldEdit only works with gzipped files).
        byteorder : str, default='big'
            Endianness of the resulting NBT Compound file ('big' or 'little', WorldEdit only works with big endian
            files).

        Returns
        -------
        nbt : nbtlib.File
            The Region represented as a Sponge Schematic NBT Compound file.
        """

        # TODO Needs unit tests

        nbt = nbtlib.File(gzipped=gzipped, byteorder=byteorder)

        nbt['DataVersion'] = Int(mc_version)
        nbt['Version'] = Int(SPONGE_VERSION)

        nbt['Width'] = Short(abs(self.__width))
        nbt['Height'] = Short(abs(self.__height))
        nbt['Length'] = Short(abs(self.__length))

        nbt['Offset'] = IntArray([Int(0), Int(0), Int(0)])  # not strictly necessary

        # process entities
        size = (self.__width, self.__height, self.__length)
        entities = List[Compound]()
        for entity in self.__entities:
            entity_cmp = Compound()
            for key, value in entity.data.items():
                entity_cmp[key] = value

            entity_cmp['Pos'] = List[Double](
                [Double(coord - (0 if dim > 0 else (dim + 1))) for coord, dim in zip(entity.position, size)])
            keys = entity.data.keys()
            if 'TileX' in keys:
                entity_cmp['TileX'] = Int(entity_cmp['Pos'][0])
                entity_cmp['TileY'] = Int(entity_cmp['Pos'][1])
                entity_cmp['TileZ'] = Int(entity_cmp['Pos'][2])

            entity_cmp['Id'] = entity_cmp['id']
            del entity_cmp['id']
            entities.append(entity_cmp)

        nbt['Entities'] = entities

        # process tile entities
        tile_entities = List[Compound]()
        for tile_entity in self.__tile_entities:
            tile_entity_cmp = Compound()
            for key, value in tile_entity.data.items():
                tile_entity_cmp[key] = value

            tile_entity_cmp['Pos'] = IntArray([Int(coord) for coord in tile_entity.position])
            for key in ['x', 'y', 'z']:
                del tile_entity_cmp[key]
            tile_entities.append(tile_entity_cmp)

        nbt['BlockEntities'] = tile_entities

        # process block palette
        nbt['PaletteMax'] = Int(len(self.__palette))
        pal = Compound()
        for i, block in enumerate(self.__palette):
            state = block.to_block_state_identifier()
            pal[state] = Int(i)

        nbt['Palette'] = pal

        # process blocks
        block_array = []
        for i in range(abs(self.__width * self.__height * self.__length)):
            blocks_per_layer = abs(self.__width * self.__length)
            y = int(i / blocks_per_layer)
            i_in_layer = i % blocks_per_layer
            z = int(i_in_layer / abs(self.__width))
            x = i_in_layer % abs(self.__width)
            block_array.append(self.__blocks[x, y, z])

        nbt['BlockData'] = ByteArray([Byte(id) for id in block_array])

        return nbt

    @staticmethod
    def from_sponge_nbt(nbt):
        """
        Returns a Litematica Region based on an NBT Compound that conforms to the Sponge Schematic Format (version 2)
        used by mods like WorldEdit (https://github.com/SpongePowered/Schematic-Specification).

        Parameters
        ----------
        nbt : nbtlib.tag.Compound
            The Sponge schematic NBT Compound.

        Returns
        -------
        region : Region
            A Litematica Region built from the Sponge schematic.
        mc_version :
            Minecraft data version that the Sponge schematic was created for.
        """

        # TODO Needs unit tests

        mc_version = nbt['DataVersion']
        width = int(nbt['Width'])
        height = int(nbt['Height'])
        length = int(nbt['Length'])
        region = Region(0, 0, 0, width, height, length)
        offset = nbt['Offset']

        # process entities
        for entity in nbt['Entities']:
            if 'Id' not in entity.keys():
                raise RequiredKeyMissingException('Id')
            entity['id'] = entity['Id']
            del entity['Id']

            ent = Entity(entity)
            ent.position = tuple([coord - off for coord, off in zip(ent.position, offset)])
            region.entities.append(ent)

        # process tile entities
        tile_entities = nbt['BlockEntities']
        for tile_entity in tile_entities:
            if 'Id' not in tile_entity.keys():
                raise RequiredKeyMissingException('Id')
            tile_entity['id'] = tile_entity['Id']
            del tile_entity['Id']

            tent = TileEntity.fromnbt(tile_entity)
            tent.position = tent.data['Pos']
            del tile_entity['Pos']
            region.tile_entities.append(tent)

        # process blocks and let setblock() automatically generate the palette
        palette = nbt['Palette']
        palette_dict = {}
        for block, index in palette.items():
            property_dict = {}
            if block.find('[') == -1:
                block_id = block
            else:
                entries = block.split('[')
                block_id = entries[0]
                properties = entries[1].replace(']', '').split(',')
                for property in properties:
                    key, value = property.split('=')
                    property_dict[key] = value

            block_state = BlockState(block_id, property_dict)
            palette_dict[int(index)] = block_state

        for i, index in enumerate(nbt['BlockData']):
            blocks_per_layer = width * length
            y = int(i / blocks_per_layer)
            i_in_layer = i % blocks_per_layer
            z = int(i_in_layer / width)
            x = i_in_layer % width
            region.setblock(x, y, z, palette_dict[int(index)])

        return region, mc_version

    def to_structure_nbt(self, mc_version=MC_DATA_VERSION, gzipped=True, byteorder='big'):
        """
        Returns the Region as an NBT Compound file that conforms to Minecraft's structure NBT files.

        Parameters
        ----------
        mc_version : int, default=info.MC_DATA_VERSION
            Minecraft data version that is being emulated (https://minecraft.fandom.com/wiki/Data_version). Should not
            be critical for newer versions of Minecraft.
        gzipped : bool, default=True
            Whether the NBT Compound file should be compressed (Vanilla Minecraft only works with gzipped files).
        byteorder : str, default='big'
            Endianness of the resulting NBT Compound file ('big' or 'little', Vanilla Minecraft only works with
            big endian files).

        Returns
        -------
        nbt : nbtlib.File
            The Region represented as a Minecraft structure NBT file.
        """

        # TODO Needs unit tests

        structure = nbtlib.File(gzipped=gzipped, byteorder=byteorder)

        structure['size'] = List[Int]([abs(self.__width), abs(self.__height), abs(self.__length)])
        structure['DataVersion'] = Int(mc_version)

        # process entities
        size = (self.__width, self.__height, self.__length)
        entities = List[Compound]()
        for entity in self.__entities:
            entity_cmp = Compound()
            entity_cmp['nbt'] = entity.data
            entity_cmp['pos'] = List[Double](
                [Double(coord - (0 if dim > 0 else (dim + 1))) for coord, dim in zip(entity.position, size)])
            entity_cmp['blockPos'] = List[Int](
                [Int(coord - (0 if dim > 0 else (dim + 1))) for coord, dim in zip(entity.position, size)])
            entities.append(entity_cmp)

        structure['entities'] = entities

        # create tile entity dictionary to add them correctly to the block list later
        tile_entity_dict = {}
        for tile_entity in self.__tile_entities:
            tile_entity_cmp = Compound()
            for key, value in tile_entity.data.items():
                if key not in ['x', 'y', 'z']:
                    tile_entity_cmp[key] = value

            tile_entity_dict[tile_entity.position] = tile_entity_cmp

        # process palette
        structure['palette'] = List[Compound]([block._tonbt() for block in self.__palette])

        # process blocks
        blocks = List[Compound]()
        for x, y, z in np.ndindex(self.__blocks.shape):
            block = Compound()
            position = (x, y, z)
            if position in tile_entity_dict.keys():
                block['nbt'] = tile_entity_dict[position]
            block['pos'] = List[Int]([Int(coord) for coord in position])
            block['state'] = Int(self.__blocks[x, y, z])
            blocks.append(block)

        structure['blocks'] = blocks

        return structure

    @staticmethod
    def from_structure_nbt(structure):
        """
        Returns a Litematica Region based on an NBT Compound that conforms to Minecraft's structure NBT files.

        Parameters
        ----------
        structure : nbtlib.tag.Compound
            The Minecraft structure NBT Compound.

        Returns
        -------
        region : Region
            A Litematica Region built from the Minecraft structure.
        mc_version :
            Minecraft data version that the structure was created for.
        """

        # TODO Needs unit tests

        mc_version = structure['DataVersion']
        size = structure['size']
        width = int(size[0])
        height = int(size[1])
        length = int(size[2])
        region = Region(0, 0, 0, width, height, length)

        # process entities
        for entity in structure['entities']:
            ent = Entity(entity['nbt'])
            ent.position = entity['pos']
            region.entities.append(ent)

        # process blocks and let setblock() automatically generate the palette
        palette = structure['palette']
        for block in structure['blocks']:
            x, y, z = block['pos']
            state = block['state']
            region.setblock(x, y, z, BlockState.fromnbt(palette[state]))
            if 'nbt' in block.keys():
                tile_entity = TileEntity(block['nbt'])
                tile_entity.position = block['pos']
                region.tile_entities.append(tile_entity)

        return region, mc_version

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
            reg.__block_ticks.append(blockTick)

        for fluidTick in nbt["PendingFluidTicks"]:
            reg.__fluid_ticks.append(fluidTick)

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
        Returns the range of coordinates this region contains along its X axis
        """
        return range(self.minx(), self.maxx() + 1)

    def yrange(self):
        """
        Returns the range of coordinates this region contains along its Y axis
        """
        return range(self.miny(), self.maxy() + 1)

    def zrange(self):
        """
        Returns the range of coordinates this region contains along its Z axis
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

    @property
    def entities(self):
        return self.__entities

    @property
    def tile_entities(self):
        return self.__tile_entities

    @property
    def block_ticks(self):
        return self.__block_ticks

    @property
    def fluid_ticks(self):
        return self.__fluid_ticks

    def as_schematic(self, name=DEFAULT_NAME, author="", description="", mc_version=MC_DATA_VERSION):
        """
        Creates and returns a schematic that contains that region at the origin.
        name: A name for both the region and the schematic
        author: an author for the schematic
        description: a description for the schematic
        """
        from .Schematic import Schematic

        return Schematic(name=name, author=author, description=description, regions={name: self}, mc_version=mc_version)