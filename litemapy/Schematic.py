from json import dumps
from math import ceil, log
from time import time

import nbtlib
import numpy as np
from nbtlib.tag import Short, Byte, Int, Long, Double, String, List, Compound, ByteArray, IntArray

from .info import *
from .Storage import LitematicaBitArray, DiscriminatingDictionary
from .Exception import CorruptedSchematicError, InvalidSchematicError
from .BlockState import BlockState


AIR = BlockState("minecraft:air")


class Schematic:
    """
    A schematic file
    """

    def __init__(self,
                 name=DEFAULT_NAME, author="", description="",
                 regions=None, lm_version=LITEMATIC_VERSION, mc_version=MC_DATA_VERSION
                 ):
        """
        Initialize a schematic of size width, height and length
        name, author and description are used in metadata
        regions should be dictionary {'regionname': region} to add to the schematic
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









