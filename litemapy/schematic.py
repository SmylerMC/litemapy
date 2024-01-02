from math import ceil, log
from time import time

import nbtlib
import numpy as np
from nbtlib.tag import Short, Byte, Int, Long, Double, String, List, Compound, ByteArray, IntArray

from .info import *
from .minecraft import BlockState, Entity, TileEntity, RequiredKeyMissingException
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

    def save(self, file_path, update_meta=True, save_soft=True, gzipped=True, byteorder='big'):
        """
        Save this schematic to a file.

        :param file_path:   the filesystem path the schematic should be saved to
        :type file_path:    str
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
        f = nbtlib.File(self.to_nbt(save_soft=save_soft), gzipped=gzipped, byteorder=byteorder)
        f.save(file_path)

    def to_nbt(self, save_soft=True):
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
        for name, region in self.regions.items():
            regs[name] = region.to_nbt()
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
        schematic = Schematic(name=name, author=author, description=desc, regions=regions, lm_version=lm_version,
                              mc_version=mc_version)
        if schematic.width != width:
            raise CorruptedSchematicError(
                "Invalid schematic width in metadata, excepted {} was {}".format(schematic.width, width))
        if schematic.height != height:
            raise CorruptedSchematicError(
                "Invalid schematic height in metadata, excepted {} was {}".format(schematic.height, height))
        if schematic.length != length:
            raise CorruptedSchematicError(
                "Invalid schematic length in metadata, excepted {} was {}".format(schematic.length, length))
        schematic.created = int(meta["TimeCreated"])
        schematic.modified = int(meta["TimeModified"])
        if "RegionCount" in meta and len(schematic.regions) != meta["RegionCount"]:
            raise CorruptedSchematicError("Number of regions in metadata does not match the number of parsed regions")
        if 'PreviewImageData' in meta.keys():
            schematic.__preview = meta['PreviewImageData']
        return schematic

    def updatemeta(self):
        """
        Update this schematic's metadata (set the modified time to the current time).
        """
        self.modified = round(time() * 1000)

    @staticmethod
    def load(file_path):
        """
        Read a schematic from a file.

        :param file_path:   the filesystem path to the file to load

        :rtype:             Schematic

        :raises CorruptedSchematicError: if the schematic file is malformed in any way
        """
        nbt = nbtlib.File.load(file_path, True)
        return Schematic.fromnbt(nbt)

    def _can_add_region(self, name, region):
        if type(name) != str:
            return False, "Region name should be a string"
        return True, ""

    def __on_region_add(self, name, region):
        if self.__x_min is None:
            self.__x_min = region.minschemx()
        else:
            self.__x_min = min(self.__x_min, region.minschemx())
        if self.__x_max is None:
            self.__x_max = region.maxschemx()
        else:
            self.__x_max = max(self.__x_max, region.maxschemx())
        if self.__y_min is None:
            self.__y_min = region.minschemy()
        else:
            self.__y_min = min(self.__y_min, region.minschemy())
        if self.__y_max is None:
            self.__y_max = region.maxschemy()
        else:
            self.__y_max = max(self.__y_max, region.maxschemy())
        if self.__z_min is None:
            self.__z_min = region.minschemz()
        else:
            self.__z_min = min(self.__z_min, region.minschemz())
        if self.__z_max is None:
            self.__z_max = region.maxschemz()
        else:
            self.__z_max = max(self.__z_max, region.maxschemz())

    def __on_region_remove(self, name, region):
        bounding_box_changed = self.__x_min == region.minschemx()
        bounding_box_changed = bounding_box_changed or self.__x_max == region.maxschemx()
        bounding_box_changed = bounding_box_changed or self.__y_min == region.minschemy()
        bounding_box_changed = bounding_box_changed or self.__y_max == region.maxschemy()
        bounding_box_changed = bounding_box_changed or self.__z_min == region.minschemz()
        bounding_box_changed = bounding_box_changed or self.__z_max == region.maxschemz()
        if bounding_box_changed:
            self.__compute_enclosure()

    def __compute_enclosure(self):
        x_min, x_max, y_min, y_max, z_min, z_max = None, None, None, None, None, None
        for region in self.__regions.values():
            x_min = min(x_min, region.minschemx()) if x_min is not None else region.minschemx()
            x_max = max(x_max, region.maxschemx()) if x_max is not None else region.maxschemx()
            y_min = min(y_min, region.minschemy()) if y_min is not None else region.minschemy()
            y_max = max(y_max, region.maxschemy()) if y_max is not None else region.maxschemy()
            z_min = min(z_min, region.minschemz()) if z_min is not None else region.minschemz()
            z_max = max(z_max, region.maxschemz()) if z_max is not None else region.maxschemz()
        self.__x_min = x_min
        self.__x_max = x_max
        self.__y_min = y_min
        self.__y_max = y_max
        self.__z_min = z_min
        self.__z_max = z_max

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
        if self.__x_min is None or self.__x_max is None:
            return 0
        return self.__x_max - self.__x_min + 1

    @property
    def height(self):
        """
        The height of this Schematic's bounding box.
        See :ref:`Coordinate systems <coordinates>`.
        This property is read-only.

        :type: int
        """
        if self.__y_min is None or self.__y_max is None:
            return 0
        return self.__y_max - self.__y_min + 1

    @property
    def length(self):
        """
        The length of this Schematic's bounding box.
        See :ref:`Coordinate systems <coordinates>`.
        This property is read-only.

        :type: int
        """
        if self.__z_min is None or self.__z_max is None:
            return 0
        return self.__z_max - self.__z_min + 1

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

    def to_nbt(self):
        """
        Write this region to an NBT tag.

        :rtype: ~nbtlib.tag.Compound
        """

        self._optimize_palette()

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

        plt = List[Compound]([blk.to_nbt() for blk in self.__palette])
        root["BlockStatePalette"] = plt

        entities = List[Compound]([entity.to_nbt() for entity in self.__entities])
        root["Entities"] = entities

        tile_entities = List[Compound]([tile_entity.to_nbt() for tile_entity in self.__tile_entities])
        root["TileEntities"] = tile_entities

        root["PendingBlockTicks"] = List[Compound](self.__block_ticks)
        root["PendingFluidTicks"] = List[Compound](self.__fluid_ticks)

        arr = LitematicaBitArray(self.getvolume(), self.__get_needed_nbits())
        for x in range(abs(self.__width)):
            for y in range(abs(self.__height)):
                for z in range(abs(self.__length)):
                    ind = (y * abs(self.__width * self.__length)) + z * abs(self.__width) + x
                    arr[ind] = int(self.__blocks[x, y, z])
        root["BlockStates"] = arr._to_nbt_long_array()

        return root

    def to_sponge_nbt(self, mc_version=MC_DATA_VERSION, gzipped=True, endianness='big'):
        """
        Returns the Region as an NBT Compound file that conforms to the Sponge Schematic Format (version 2) used by mods
        like WorldEdit.
        Check `the file format specification <https://github.com/SpongePowered/Schematic-Specification>`_
        for more information.

        :param mc_version:  Minecraft data version that is being emulated
                            (https://minecraft.wiki/w/Data_version).
                            Should not be critical for newer versions of Minecraft.
        :type mc_version:   int
        :param gzipped:     Whether the NBT Compound file should be compressed
                            (WorldEdit only works with gzipped files).
        :type gzipped:      bool
        :param endianness:  Endianness of the resulting NBT Compound file
                            ('big' or 'little', WorldEdit only works with big endian files).
        :type endianness:   str

        :returns:           The Region represented as a Sponge Schematic NBT Compound file.
        :rtype:             ~nbtlib.nbt.File
        """

        self._optimize_palette()

        # TODO Needs unit tests

        nbt = nbtlib.File(gzipped=gzipped, byteorder=endianness)

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
            entity_tag = Compound()
            for key, value in entity.data.items():
                entity_tag[key] = value

            entity_tag['Pos'] = List[Double](
                [Double(coord - (0 if dim > 0 else (dim + 1))) for coord, dim in zip(entity.position, size)])
            keys = entity.data.keys()
            if 'TileX' in keys:
                entity_tag['TileX'] = Int(entity_tag['Pos'][0])
                entity_tag['TileY'] = Int(entity_tag['Pos'][1])
                entity_tag['TileZ'] = Int(entity_tag['Pos'][2])

            entity_tag['Id'] = entity_tag['id']
            del entity_tag['id']
            entities.append(entity_tag)

        nbt['Entities'] = entities

        # process tile entities
        tile_entities = List[Compound]()
        for tile_entity in self.__tile_entities:
            tile_entity_tag = Compound()
            for key, value in tile_entity.data.items():
                tile_entity_tag[key] = value

            tile_entity_tag['Pos'] = IntArray([Int(coord) for coord in tile_entity.position])
            for key in ['x', 'y', 'z']:
                del tile_entity_tag[key]
            tile_entities.append(tile_entity_tag)

        nbt['BlockEntities'] = tile_entities

        # process block palette
        nbt['PaletteMax'] = Int(len(self.__palette))
        palette = Compound()
        for i, block in enumerate(self.__palette):
            state = block.to_block_state_identifier()
            palette[state] = Int(i)

        nbt['Palette'] = palette

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

            block_state = BlockState(block_id, **property_dict)
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
                            (https://minecraft.wiki/w/Data_version).
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

        self._optimize_palette()

        structure = nbtlib.File(gzipped=gzipped, byteorder=byteorder)

        structure['size'] = List[Int]([abs(self.__width), abs(self.__height), abs(self.__length)])
        structure['DataVersion'] = Int(mc_version)

        # process entities
        size = (self.__width, self.__height, self.__length)
        entities = List[Compound]()
        for entity in self.__entities:
            entity_tag = Compound()
            entity_tag['nbt'] = entity.data
            entity_tag['pos'] = List[Double](
                [Double(coord - (0 if dim > 0 else (dim + 1))) for coord, dim in zip(entity.position, size)])
            entity_tag['blockPos'] = List[Int](
                [Int(coord - (0 if dim > 0 else (dim + 1))) for coord, dim in zip(entity.position, size)])
            entities.append(entity_tag)

        structure['entities'] = entities

        # create tile entity dictionary to add them correctly to the block list later
        tile_entity_dict = {}
        for tile_entity in self.__tile_entities:
            tile_entity_tag = Compound()
            for key, value in tile_entity.data.items():
                if key not in ['x', 'y', 'z']:
                    tile_entity_tag[key] = value

            tile_entity_dict[tile_entity.position] = tile_entity_tag

        # process palette
        structure['palette'] = List[Compound]([block.to_nbt() for block in self.__palette])

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
        x, y, z = self.__region_coordinates_to_store_coordinates(x, y, z)
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
        x, y, z = self.__region_coordinates_to_store_coordinates(x, y, z)
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

        # air is index zero
        return np.count_nonzero(self.__blocks)

    def __region_coordinates_to_store_coordinates(self, x, y, z):
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
        region = Region(x, y, z, width, height, length)
        del region.__palette[0]
        for block_nbt in nbt["BlockStatePalette"]:
            block = BlockState.fromnbt(block_nbt)
            region.__palette.append(block)

        for entity_nbt in nbt["Entities"]:
            entity = Entity.fromnbt(entity_nbt)
            region.entities.append(entity)

        for tile_entity_nbt in nbt["TileEntities"]:
            block = TileEntity.fromnbt(tile_entity_nbt)
            region.tile_entities.append(block)

        blocks = nbt["BlockStates"]
        nbits = region.__get_needed_nbits()
        bit_array = LitematicaBitArray.from_nbt_long_array(blocks, region.getvolume(), nbits)
        for x in range(abs(width)):
            for y in range(abs(height)):
                for z in range(abs(length)):
                    ind = (y * abs(width * length)) + z * abs(width) + x
                    region.__blocks[x][y][z] = bit_array[ind]

        for block_ticks in nbt["PendingBlockTicks"]:
            region.__block_ticks.append(block_ticks)

        for fluid_ticks in nbt["PendingFluidTicks"]:
            region.__fluid_ticks.append(fluid_ticks)

        return region

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

        :type: int
        """
        return self.__x

    @property
    def y(self):
        """
        The Y coordinate of the region within the schematic's coordinate system.
        This property is read only.

        :type: int
        """
        return self.__y

    @property
    def z(self):
        """
        The Z coordinate of the region within the schematic's coordinate system.
        The property is read only.

        :type: int
        """
        return self.__z

    @property
    def width(self):
        """
        The width of the region.
        This property is read only.

        :type: int
        """
        return self.__width

    @property
    def height(self):
        """
        The height of the region.
        This property is read only.

        :type: int
        """
        return self.__height

    @property
    def length(self):
        """
        The length of the region.
        This property is read only.

        :type: int
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

    @property
    def palette(self):
        """
        The palette used to store blocks within the region.
        Each entry in the palette is assured to be unique.
        Expected the first palette entry which is always "minecraft:air",
        each entry is assured to have at least one instance in the region.

        :type: tuple[BlockState]
        """
        self._optimize_palette()
        return tuple(self.__palette)

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

    def __replace_palette_index(self, old_index: int, new_index: int):
        if old_index == new_index:
            return
        self.__blocks[self.__blocks == old_index] = new_index

    def _optimize_palette(self):
        new_palette = []
        for old_index, state in enumerate(self.__palette):
            if old_index != 0 and old_index not in self.__blocks:
                # Non-air block that no longer exists in the schematic
                continue
            for i, other_state in enumerate(new_palette):
                if state == other_state:
                    new_index = i
                    break
            else:
                new_index = len(new_palette)
                new_palette.append(state)
            self.__replace_palette_index(old_index, new_index)
        self.__palette = new_palette

    def filter(self, function):
        """
        Replaces all occurrences of :class:`BlockState` with others by providing a mapping function.
        This method works with the palette directly and the mapping function is therefore only called
        once per block state type in the region, and not for every position.
        This is a lot faster than manually iterating over region coordinates.

        :param function: a mapping function
        :type function:  (BlockState) -> BlockState
        """
        self.__palette = list(map(function, self.__palette))

        # We need to ensure we always have air at palette index 0
        if self.__palette[0] != AIR:
            self.__palette.append(self.__palette[0])
            self.__replace_palette_index(0, len(self.__palette) - 1)
            self.__palette[0] = AIR

        # The filter function may have introduced duplicates in the palette
        self._optimize_palette()


AIR = BlockState("minecraft:air")


class CorruptedSchematicError(Exception):
    pass
