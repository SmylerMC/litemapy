import unittest
from litemapy import Schematic, Region
from os import walk
from .constants import *

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
