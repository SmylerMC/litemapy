import unittest
from litemapy import Schematic, Region
from os import walk
from .constants import *
import random
from . import helper

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
        reg = Region(0, 0, 0, 10, 10, 10)
        self.assertEqual(reg.minschemx(), 0)
        self.assertEqual(reg.maxschemx(), 9)
        self.assertEqual(reg.minschemy(), 0)
        self.assertEqual(reg.maxschemy(), 9)
        self.assertEqual(reg.minschemz(), 0)
        self.assertEqual(reg.maxschemz(), 9)
        self.assertEqual(reg.minx(), 0)
        self.assertEqual(reg.maxx(), 9)
        self.assertEqual(reg.miny(), 0)
        self.assertEqual(reg.maxy(), 9)
        self.assertEqual(reg.minz(), 0)
        self.assertEqual(reg.maxz(), 9)
        reg = Region(0, 0, 0, -10, -10, -10)
        self.assertEqual(reg.minschemx(), -9)
        self.assertEqual(reg.maxschemx(), 0)
        self.assertEqual(reg.minschemy(), -9)
        self.assertEqual(reg.maxschemy(), 0)
        self.assertEqual(reg.minschemz(), -9)
        self.assertEqual(reg.maxschemz(), 0)
        self.assertEqual(reg.minx(), -9)
        self.assertEqual(reg.maxx(), 0)
        self.assertEqual(reg.miny(), -9)
        self.assertEqual(reg.maxy(), 0)
        self.assertEqual(reg.minz(), -9)
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
