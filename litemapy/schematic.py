from json import dumps
from math import ceil, log
from time import time

import nbtlib
import numpy as np
from nbtlib.tag import Short, Byte, Int, Long, Double, String, List, Compound, ByteArray, IntArray

from .info import *
from .storage import LitematicaBitArray, DiscriminatingDictionary


class Schematic:
    """
    Represents a schematic file in the Litematic format.
    """

    def __init__(self,
                 name=DEFAULT_NAME, author="", description="",
                 regions=None, lm_version=LITEMATIC_VERSION, mc_version=MC_DATA_VERSION
                 ):
        """
        Schematic can be created by optionally providing metadata and regions, or leaving them blank or default.

        :param name:        The name of the schematic to write in the metadata
        :type name:         str
        :param author:      The name of the author to write in the metadata
        :type author:       str
        :param description: The description to write in the metadata
        :type description:  str
        :param regions:     Regions to populate the schematic with
        :type regions:      dict[str, Region]
        :param lm_version:  The litematic version (you are unlikely to ever need to use this)
        :type lm_version:   int
        :param mc_version:  The Minecraft data version (you are unlikely to ever need to use this)
        :type mc_version:   int
        """
        if regions is None:
            regions = {}
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
        Save this schematic to a file.

        :param fname:       the filesystem path the schematic should be saved to
        :type fname:        str
        :param update_meta: whether to update the schematic's metadata before saving
                            (see :func:`~litemapy.Schematic.updatemeta`)
        :type update_meta:  bool
        :param save_soft:   whether to add an entry to the metadata indicating the schematic was created with Litemapy
        :type save_soft:    bool
        :param gzipped:     whether to compress the NBT content with gzip (this is the normal behavior)
        :type gzipped:      bool
        :param byteorder:   endianness of NBT numbers (either "little" or "big", default is "big")
        :type byteorder:    str

        :raises ValueError: if this schematic does not have any region
        """
        if update_meta:
            self.updatemeta()
        f = nbtlib.File(self._tonbt(save_soft=save_soft), gzipped=gzipped, byteorder=byteorder)
        f.save(fname)

    def _tonbt(self, save_soft=True):
        """
        Write the schematic to an NBT tag.

        :param save_soft:   whether to add an entry to the metadata indicating the schematic was created with Litemapy
        :type save_soft:    bool

        :rtype: ~nbtlib.tag.Compound

        :raises ValueError: if this schematic does not have any region
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
        Read a schematic from an NBT tag.

        :param nbt: a schematic serialized as an NBT tag
        :type nbt:  ~nbtlib.tag.Compound

        :rtype:     Schematic

        :raises CorruptedSchematicError: if the schematic tag is malformed
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
        sch = Schematic(name=name, author=author, description=desc, regions=regions, lm_version=lm_version,
                        mc_version=mc_version)
        if sch.width != width:
            raise CorruptedSchematicError(
                "Invalid schematic width in metadata, excepted {} was {}".format(sch.width, width))
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
        Update this schematic's metadata (set the modified time to the current time).
        """
        self.modified = round(time() * 1000)

    @staticmethod
    def load(fname):
        """
        Read a schematic from a file.

        :param fname:   the filesystem path to the file to load

        :rtype:         Schematic

        :raises CorruptedSchematicError: if the schematic file is malformed in any way
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
        """
        The regions in this schematic, as a dictionary.
        This is a read only property, and it is not possible to replace this dictionary.
        It can however be edited, as long as the suitable types are used.
        Using an incorrect type will raise a :class:`~litemapy.storage.DiscriminationError`.

        :type: dict[str, Region]
        """
        return self.__regions

    @property
    def width(self):
        """
        The width of this Schematic's bounding box.
        See :ref:`Coordinate systems <coordinates>`.
        This property is read-only.

        :type: int
        """
        if self.__xmin is None or self.__xmax is None:
            return 0
        return self.__xmax - self.__xmin + 1

    @property
    def height(self):
        """
        The height of this Schematic's bounding box.
        See :ref:`Coordinate systems <coordinates>`.
        This property is read-only.

        :type: int
        """
        if self.__ymin is None or self.__ymax is None:
            return 0
        return self.__ymax - self.__ymin + 1

    @property
    def length(self):
        """
        The length of this Schematic's bounding box.
        See :ref:`Coordinate systems <coordinates>`.
        This property is read-only.

        :type: int
        """
        if self.__zmin is None or self.__zmax is None:
            return 0
        return self.__zmax - self.__zmin + 1

    @property
    def preview(self):
        # TODO This is not documented on purpose because ideally we would make it return a usable Pillow Image object.
        return self.__preview

    @preview.setter
    def preview(self, value):
        self.__preview = value


class Region:
    """
    Represents a schematic region.
    """

    def __init__(self, x, y, z, width, height, length):
        """
        :param x:       the X coordinate of the region in the schematic
        :type x:        int
        :param y:       the Y coordinate of the region in the schematic
        :type y:        int
        :param z:       the Z coordinate of the region in the schematic
        :type z:        int
        :param width:   the size of the region along the x-axis (can be negative!)
        :type width:    int
        :param height:  the size of the region along the y-axis (can be negative!)
        :type height:   int
        :param length:  the size of the region along the z-axis (can be negative!)
        :type length:   int

        :raises ValueError: if either width, height or length is 0
        """
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
        Write this region to an NBT tag.

        :rtype: ~nbtlib.tag.Compound
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
        like WorldEdit.
        Check `the file format specification <https://github.com/SpongePowered/Schematic-Specification>`_
        for more information.

        :param mc_version:  Minecraft data version that is being emulated
                            (https://minecraft.fandom.com/wiki/Data_version).
                            Should not be critical for newer versions of Minecraft.
        :type mc_version:   int
        :param gzipped:     Whether the NBT Compound file should be compressed
                            (WorldEdit only works with gzipped files).
        :type gzipped:      bool
        :param byteorder:   Endianness of the resulting NBT Compound file
                            ('big' or 'little', WorldEdit only works with big endian files).
        :type byteorder:    str

        :returns:           The Region represented as a Sponge Schematic NBT Compound file.
        :rtype:             ~nbtlib.nbt.File
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
        used by mods like WorldEdit.
        Check `the file format specification <https://github.com/SpongePowered/Schematic-Specification>`_
        for more information.

        :param nbt: The Sponge schematic NBT Compound.
        :type nbt:  nbtlib.tag.Compound

        :returns:   a Litematica Region built from the Sponge schematic
                    and the Minecraft data version that the Sponge schematic was created for.
        :rtype:     tuple[Region, int]
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

        :param mc_version:  Minecraft data version that is being emulated
                            (https://minecraft.fandom.com/wiki/Data_version).
                            Should not be critical for newer versions of Minecraft.
        :type mc_version:   int
        :param gzipped:     Whether the NBT Compound file should be compressed
                            (Vanilla Minecraft only works with gzipped files).
        :type gzipped:      bool
        :param byteorder:   Endianness of the resulting NBT Compound file
                            ('big' or 'little', Vanilla Minecraft only works with big endian files).
        :type byteorder:    str

        :returns:           The Region represented as a Minecraft structure NBT file.
        :rtype:             ~nbtlib.nbt.File
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

        :param structure:   The Minecraft structure NBT Compound.
        :type structure:    ~nbtlib.tag.Compound

        :returns:           A Litematica Region built from the Minecraft structure
                            and the Minecraft data version that the structure was created for
        :rtype:             tuple[Region, str]
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
        Get a :class:`~litemapy.BlockState` in the region.

        :param x:   the X coordinate to get the block at
        :type x:    int
        :param y:   the Y coordinate to get the block at
        :type y:    int
        :param z:   the Z coordinate to get the block at
        :type z:    int

        :rtype:     ~litemapy.BlockState
        """
        x, y, z = self.__regcoordinates2storecoords(x, y, z)
        return self.__palette[self.__blocks[x, y, z]]

    def setblock(self, x, y, z, block):
        """
        Set a :class:`~litemapy.BlockState` in the region.

        :param x:       the X coordinate to set the block at
        :type x:        int
        :param y:       the Y coordinate to set the block at
        :type y:        int
        :param z:       the Z coordinate to set the block at
        :type z:        int
        :param block:   the new block state
        :type block:    ~litemapy.BlockState
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
        Counts the number of blocks in the region.

        :returns: the number of non-air blocks in the region
        :rtype: int
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
        Computes this region's volume.

        :returns: this region volume in blocks
        :rtype: int
        """
        return abs(self.__width * self.__height * self.__length)

    def __get_needed_nbits(self):
        return max(ceil(log(len(self.__palette), 2)), 2)

    @staticmethod
    def fromnbt(nbt):
        """
        Read a region from an NBT tag.

        :param nbt: an NBT tag to read the region from
        :type nbt:  ~nbtlib.tag.Compound

        :rtype:     Region
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
        :returns:   the minimum X coordinate of this region in the schematics coordinate system
        :rtype:     int
        """
        return min(self.__x, self.__x + self.width + 1)

    def maxschemx(self):
        """
        :returns:   the maximum X coordinate of this region in the schematics coordinate system
        :rtype:     int
        """
        return max(self.__x, self.__x + self.width - 1)

    def minschemy(self):
        """
        :returns:   the minimum Y coordinate of this region in the schematics coordinate system
        :rtype:     int
        """
        return min(self.__y, self.__y + self.height + 1)

    def maxschemy(self):
        """
        :returns:   the maximum Y coordinate of this region in the schematics coordinate system
        :rtype:     int
        """
        return max(self.__y, self.__y + self.height - 1)

    def minschemz(self):
        """
        :returns:   the minimum Z coordinate of this region in the schematics coordinate system
        :rtype:     int
        """
        return min(self.__z, self.__z + self.length + 1)

    def maxschemz(self):
        """
        :returns:   the maximum Z coordinate of this region in the schematics coordinate system
        :rtype:     int
        """
        return max(self.__z, self.__z + self.length - 1)

    def minx(self):
        """
        :returns:   the minimum X coordinate of this region in its own coordinate system
        :rtype:     int
        """
        return min(0, self.width + 1)

    def maxx(self):
        """
        :returns:   the maximum X coordinate of this region in its own coordinate system
        :rtype:     int
        """
        return max(0, self.width - 1)

    def miny(self):
        """
        :returns:   the minimum Y coordinate of this region in its own coordinate system
        :rtype:     int
        """
        return min(0, self.height + 1)

    def maxy(self):
        """
        :returns:   the maximum Y coordinate of this region in its own coordinate system
        :rtype:     int
        """
        return max(0, self.height - 1)

    def minz(self):
        """
        :returns:   the minimum Z coordinate of this region in its own coordinate system
        :rtype:     int
        """
        return min(0, self.length + 1)

    def maxz(self):
        """
        :returns:   the maximum Z coordinate of this region in its own coordinate system
        :rtype:     int
        """
        return max(0, self.length - 1)

    def xrange(self):
        """
        :returns:   the range of coordinates this region contains along its X axis
        :rtype:     range
        """
        return range(self.minx(), self.maxx() + 1)

    def yrange(self):
        """
        :returns:   the range of coordinates this region contains along its Y axis
        :rtype:     range
        """
        return range(self.miny(), self.maxy() + 1)

    def zrange(self):
        """
        :returns:   the range of coordinates this region contains along its Z axis
        :rtype:     range
        """
        return range(self.minz(), self.maxz() + 1)

    def allblockpos(self):
        """
        :returns:   an iterator over the coordinates this region contains in its own coordinate system
        :rtype:     ~collections.abc.Iterator[tuple[int, int, int]]
        """
        for x in self.xrange():
            for y in self.yrange():
                for z in self.zrange():
                    yield x, y, z

    @property
    def x(self):
        """
        The X coordinate of the region within the schematic's coordinate system.
        This property is read only.
        :type:  int
        """
        return self.__x

    @property
    def y(self):
        """
        The Y coordinate of the region within the schematic's coordinate system.
        This property is read only.
        :type:  int
        """
        return self.__y

    @property
    def z(self):
        """
        The Z coordinate of the region within the schematic's coordinate system.
        The property is read only.
        :type:  int
        """
        return self.__z

    @property
    def width(self):
        """
        The width of the region.
        This property is read only.
        :type:  int
        """
        return self.__width

    @property
    def height(self):
        """
        The height of the region.
        This property is read only.
        :type:  int
        """
        return self.__height

    @property
    def length(self):
        """
        The length of the region.
        This property is read only.
        :type:  int
        """
        return self.__length

    @property
    def entities(self):
        """
        The entities within the region.
        :type: list[Entity]
        """
        return self.__entities

    @property
    def tile_entities(self):
        """
        The tile entities within the region.
        :type: list[TileEntity]
        """
        return self.__tile_entities

    @property
    def block_ticks(self):
        # TODO We are not exporting the documentation for this because it still exposes the raw NBT data
        return self.__block_ticks

    @property
    def fluid_ticks(self):
        # TODO We are not exporting the documentation for this because it still exposes the raw NBT data
        return self.__fluid_ticks

    def as_schematic(self, name=DEFAULT_NAME, author="", description="", mc_version=MC_DATA_VERSION):
        """
        Creates a schematic that contains that region at the origin.

        :param name:        a name for both the region and the schematic
        :type name:         str
        :param author:      an author for the schematic
        :type author:       str
        :param description: a description for the schematic
        :type description:  str
        :param mc_version:  The Minecraft data version (you are unlikely to ever need to use this)
        :type mc_version:   int

        :rtype:             Schematic
        """
        return Schematic(name=name, author=author, description=description, regions={name: self}, mc_version=mc_version)


class BlockState:

    """
    Represents an in-game block.
    :class:`BlockState` are immutable.
    """

    def __init__(self, blockid, properties=None):
        """
        A block state has a block ID and a dictionary of properties.

        :param blockid:     the identifier of the block (e.g. *minecraft:stone*)
        :type blockid:      str
        :param properties:  the properties of the block state (e.g. *{"facing": "north"}*)
        :type properties:   dict[str, str]
        """
        if properties is None:
            properties = {}
        self.__blockid = blockid
        self.__properties = DiscriminatingDictionary(self.__validate, properties)

    def _tonbt(self):
        """
        Writes this block state to an nbt tag.

        :rtype: ~nbtlib.tag.Compound
        """
        root = Compound()
        root["Name"] = String(self.blockid)
        properties = {String(k): String(v) for k, v in self.__properties.items()}
        if len(properties) > 0:
            root["Properties"] = Compound(properties)
        return root

    @staticmethod
    def fromnbt(nbt):
        """
        Reads a :class:`BlockState` from an nbt tag.

        :rtype: BlockState
        """
        bid = str(nbt["Name"])
        if "Properties" in nbt:
            properties = {str(k): str(v) for k, v in nbt["Properties"].items()}
        else:
            properties = {}
        block = BlockState(bid, properties=properties)
        return block

    @property
    def blockid(self):
        """
        The block's identifier.

        :type:  str
        """
        return self.__blockid

    def __validate(self, k, v):
        if type(k) is not str or type(v) is not str:
            return False, "Blockstate properties should be a string => string dictionary"
        return True, ""

    def to_block_state_identifier(self, skip_empty=True):
        """
        Returns an identifier that represents the BlockState in the Sponge Schematic Format (version 2).
        Format: block_type[properties]
        Example: minecraft:oak_sign[rotation=0,waterlogged=false]

        :param skip_empty:  Whether empty brackets should be excluded if the BlockState has no properties.
        :type skip_empty:   bool

        :returns: An identifier that represents the BlockState in a Sponge schematic.
        :rtype: str
        """

        # TODO Needs unit tests

        identifier = self.__blockid
        if skip_empty and not len(self.__properties):
            return identifier

        state = dumps(self.__properties, separators=(',', '='), sort_keys=True)
        state = state.replace('{', '[').replace('}', ']')
        state = state.replace('"', '').replace("'", '')

        identifier += state
        return identifier

    def __eq__(self, other):
        if not isinstance(other, BlockState):
            raise ValueError("Can only compare blockstates with blockstates")
        return other.__blockid == self.__blockid and other.__properties == self.__properties

    def __repr__(self):
        return self.to_block_state_identifier(skip_empty=True)

    def __getitem__(self, key):
        return self.__properties[key]

    def __len__(self):
        return len(self.__properties)


class Entity:

    """
    A Minecraft entity.
    Each entitiy is identified by a type identifier (e.g. minecraft:skeleton)
    and has a position within a region, as well as a rotation and a velocity vector.
    Most also have arbitrary data depending on their type
    (e.g. a sheep has a tag for its color and one indicating whether it has been sheared).
    """

    # TODO Needs unit tests

    def __init__(self, str_or_nbt):
        # TODO Refactor to only have a from_nbt static method instead of allowing nbt into the constructor
        """
        :param str_or_nbt:  either the entity identifier as a string, in which case all other tag will be default,
                            or an bnt compound tag with the entitie's data.
        :type str_or_nbt:   ~typing.Union[str, ~nbtlib.tag.Compound]
        """

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
        """
        Save this entity as an NBT tag.

        :rtype: ~nbtlib.tag.Compound
        """
        return self._data

    @staticmethod
    def fromnbt(nbt):
        """
        Read an entity from an nbt tag.

        :param nbt: An NBT tag with the entity's data
        :type nbt:  ~nbtlib.tag.Compound

        :rtype:     Entity
        """
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
        # TODO Not documented because it exposes NBT
        return self._data

    @data.setter
    def data(self, data):
        # TODO Not documented because it exposes NBT
        self._data = Entity(data).data
        self._id = str(self._data['id'])
        self._position = tuple([float(coord) for coord in self._data['Pos']])
        self._rotation = tuple([float(coord) for coord in self._data['Rotation']])
        self._motion = tuple([float(coord) for coord in self._data['Motion']])

    @property
    def id(self):
        """
        This entity's type identifier (e.g. *minecraft:pig* )

        :type: str
        """
        return self._id

    @id.setter
    def id(self, id):
        self._id = id
        self._data['id'] = String(self._id)

    @property
    def position(self):
        """
        The position of the entity.

        :type:  tuple[float, float, float]
        """
        return self._position

    @position.setter
    def position(self, position):
        self._position = position
        self._data['Pos'] = List[Double]([Double(coord) for coord in self._position])

    @property
    def rotation(self):
        """
        The rotation of the entity.

        :type:  tuple[float, float, float]
        """
        return self._rotation

    @rotation.setter
    def rotation(self, rotation):
        self._rotation = rotation
        self._data['Rotation'] = List[Double]([Double(coord) for coord in self._rotation])

    @property
    def motion(self):
        """
        The velocity vector of the entity.

        :type:  tuple[float, float, float]
        """
        return self._motion

    @motion.setter
    def motion(self, motion):
        self._motion = motion
        self._data['Motion'] = List[Double]([Double(coord) for coord in self._motion])


class TileEntity:

    # TODO Needs unit tests
    """
    A tile entity, also often referred to as block entities,
    is a type of entity which complements a block state to store additional data
    (e.g. containers like chest both have a block state that stores properties
    like their id ( *minecraft:chest* ) and orientation, and tile entity that stores their content.
    For this reason, the :class:`TileEntity` class does not store an ID  but only a position.
    The ID can be inferred by looking up the :class:`BlockState` as the same position in the :class:`Region`.
    """

    def __init__(self, nbt):
        # TODO Not documented because it only exposes NBT
        self._data = nbt
        keys = self._data.keys()

        if 'x' not in keys:
            self._data['x'] = Int(0)
        if 'y' not in keys:
            self._data['y'] = Int(0)
        if 'z' not in keys:
            self._data['z'] = Int(0)

        self._position = tuple([int(self._data[coord]) for coord in ['x', 'y', 'z']])

    def _tonbt(self):
        """
        Saves the tile entity to a an nbt tag.

        :rtype: ~nbtlib.tag.Compound
        """
        return self._data

    @staticmethod
    def fromnbt(nbt):
        """
        Reads a tile entity from an NBT tag.

        :param nbt: the tile entity's data as an NBT tag
        :type nbt:  ~nbtlib.tag.Compound
        :rtype:     TileEntity
        """
        return TileEntity(nbt)

    def add_tag(self, key, tag):
        # TODO Not documented because it exposes NBT
        self._data[key] = tag

        pos = self._position
        if key == 'x':
            self._position = (int(tag), pos[1], pos[2])
        if key == 'y':
            self._position = (pos[0], int(tag), pos[2])
        if key == 'z':
            self._position = (pos[0], pos[1], int(tag))

    def get_tag(self, key):
        # TODO Not documented because it exposes NBT
        try:
            return self._data[key]
        except KeyError:
            raise

    @property
    def data(self):
        # TODO Not documented because it exposes NBT
        return self._data

    @data.setter
    def data(self, data):
        self._data = TileEntity(data).data
        self._position = tuple([int(self._data[coord]) for coord in ['x', 'y', 'z']])

    @property
    def position(self):
        """
        The tile entity's position within the :class:`Region`/

        :type:  tuple[int, int, int]
        """
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
