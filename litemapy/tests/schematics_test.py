import unittest
from litemapy import Schematic, Region, BlockState
from os import walk
from .constants import *
import random
from . import helper
from tempfile import TemporaryDirectory

class TestAgainstSchematics(unittest.TestCase):

    def setUp(self):
        self.validfiles = []
        for dir, dnames, fnames in walk(VALID_LITEMATIC_DIRECTORY):
            for fname in fnames:
                self.validfiles.append(dir + "/" + fname)

    def test_valid_litematics(self):
        for fname in self.validfiles:
            schem = Schematic.load(fname)

class TestMaking(unittest.TestCase):

    def test_size(self):
        sch = Schematic()
        self.assertEqual(sch.width, 0)
        self.assertEqual(sch.height, 0)
        self.assertEqual(sch.length, 0)
        reg1 = Region(0, 0, 0, 10, 10, 10)
        reg2 = Region(90, 0, 0, 10, 10, 10)
        reg3 = Region(50, 0, 0, 10, 10, 10)
        reg4 = Region(49, 0, 0, -10, 10, 10)
        sch.regions["a"] = reg1
        self.assertEqual(sch.width, 10)
        self.assertEqual(sch.height, 10)
        self.assertEqual(sch.length, 10)
        sch.regions["b"] = reg2
        self.assertEqual(sch.width, 100)
        sch.regions["c"] = reg3
        self.assertEqual(sch.width, 100)
        del sch.regions["b"]
        self.assertEqual(sch.width, 60)
        sch.regions["c"] = reg4
        self.assertEqual(sch.width, 50)

    def test_reg_min_max(self):
        reg = Region(0, 0, 0, 10, 20, 30)
        self.assertEqual(reg.minschemx(), 0)
        self.assertEqual(reg.maxschemx(), 9)
        self.assertEqual(reg.minschemy(), 0)
        self.assertEqual(reg.maxschemy(), 19)
        self.assertEqual(reg.minschemz(), 0)
        self.assertEqual(reg.maxschemz(), 29)
        self.assertEqual(reg.minx(), 0)
        self.assertEqual(reg.maxx(), 9)
        self.assertEqual(reg.miny(), 0)
        self.assertEqual(reg.maxy(), 19)
        self.assertEqual(reg.minz(), 0)
        self.assertEqual(reg.maxz(), 29)
        reg = Region(0, 0, 0, -10, -20, -30)
        self.assertEqual(reg.minschemx(), -9)
        self.assertEqual(reg.maxschemx(), 0)
        self.assertEqual(reg.minschemy(), -19)
        self.assertEqual(reg.maxschemy(), 0)
        self.assertEqual(reg.minschemz(), -29)
        self.assertEqual(reg.maxschemz(), 0)
        self.assertEqual(reg.minx(), -9)
        self.assertEqual(reg.maxx(), 0)
        self.assertEqual(reg.miny(), -19)
        self.assertEqual(reg.maxy(), 0)
        self.assertEqual(reg.minz(), -29)
        self.assertEqual(reg.maxz(), 0)
        reg = Region(10, 10, 10, 10, 10, 10)
        self.assertEqual(reg.minschemx(), 10)
        self.assertEqual(reg.maxschemx(), 19)
        self.assertEqual(reg.minschemy(), 10)
        self.assertEqual(reg.maxschemy(), 19)
        self.assertEqual(reg.minschemz(), 10)
        self.assertEqual(reg.maxschemz(), 19)
        self.assertEqual(reg.minx(), 0)
        self.assertEqual(reg.maxx(), 9)
        self.assertEqual(reg.miny(), 0)
        self.assertEqual(reg.maxy(), 9)
        self.assertEqual(reg.minz(), 0)
        self.assertEqual(reg.maxz(), 9)
        reg = Region(-10, -10, -10, 10, 10, 10)
        self.assertEqual(reg.minschemx(), -10)
        self.assertEqual(reg.maxschemx(), -1)
        self.assertEqual(reg.minschemy(), -10)
        self.assertEqual(reg.maxschemy(), -1)
        self.assertEqual(reg.minschemz(), -10)
        self.assertEqual(reg.maxschemz(), -1)
        self.assertEqual(reg.minx(), 0)
        self.assertEqual(reg.maxx(), 9)
        self.assertEqual(reg.miny(), 0)
        self.assertEqual(reg.maxy(), 9)
        self.assertEqual(reg.minz(), 0)
        self.assertEqual(reg.maxz(), 9)
        reg = Region(-10, -10, -10, -10, -10, -10)
        self.assertEqual(reg.minschemx(), -19)
        self.assertEqual(reg.maxschemx(), -10)
        self.assertEqual(reg.minschemy(), -19)
        self.assertEqual(reg.maxschemy(), -10)
        self.assertEqual(reg.minschemz(), -19)
        self.assertEqual(reg.maxschemz(), -10)
        self.assertEqual(reg.minx(), -9)
        self.assertEqual(reg.maxx(), 0)
        self.assertEqual(reg.miny(), -9)
        self.assertEqual(reg.maxy(), 0)
        self.assertEqual(reg.minz(), -9)
        self.assertEqual(reg.maxz(), 0)

    def test_random_write_read(self):
        dir = TemporaryDirectory()
        for i in range(100):
            writeschem = helper.randomschematic()
            fname = dir.name + "/" + writeschem.name + ".litematic"
            writeschem.save(fname)
            readschem = Schematic.load(fname)
            self.assertEqual(writeschem.name, readschem.name)
            self.assertEqual(writeschem.author, readschem.author)
            self.assertEqual(writeschem.description, readschem.description)
            self.assertEqual(writeschem.width, readschem.width)
            self.assertEqual(writeschem.height, readschem.height)
            self.assertEqual(writeschem.length, readschem.length)
            self.assertEqual(len(writeschem.regions), len(readschem.regions))
            for name, wreg in writeschem.regions.items():
                rreg = readschem.regions[name]
                self.assertEqual(wreg.minx(), rreg.minx())
                self.assertEqual(wreg.maxx(), rreg.maxx())
                self.assertEqual(wreg.miny(), rreg.miny())
                self.assertEqual(wreg.maxy(), rreg.maxy())
                self.assertEqual(wreg.minz(), rreg.minz())
                self.assertEqual(wreg.maxz(), rreg.maxz())
                self.assertEqual(wreg.minschemx(), rreg.minschemx())
                self.assertEqual(wreg.maxschemx(), rreg.maxschemx())
                self.assertEqual(wreg.minschemy(), rreg.minschemy())
                self.assertEqual(wreg.maxschemy(), rreg.maxschemy())
                self.assertEqual(wreg.minschemz(), rreg.minschemz())
                self.assertEqual(wreg.maxschemz(), rreg.maxschemz())
                for x, y, z in wreg.allblockpos():
                    ws = wreg.getblock(x, y, z)
                    rs = rreg.getblock(x, y, z)
                    self.assertEqual(ws, rs)
        dir.cleanup()

class TestBlockStates(unittest.TestCase):

    def test(self):
        prop = {"test1": "testval", "test2": "testval2"}
        b = BlockState("minecraft:stone", properties=prop)
        self.assertEqual(len(prop), len(b))
        for k, v in prop.items():
            self.assertEqual(b[k], v)
        nbt = b._tonbt()
        print(nbt)
        b2 = BlockState.fromnbt(nbt)
        self.assertEqual(b, b2)

