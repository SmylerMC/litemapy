import unittest
import litemapy.storage as storage
import math
from . import helper

@unittest.skipUnless(helper.java_test_available(), "Cannot run java in this environment")
class TestAgainstJavaLitematica(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.subproc, cls.gateway = helper.get_litematica_jvm()
        cls.JLitematicaBitArray = cls.gateway.jvm.fi.dy.masa.litematica.schematic.container.LitematicaBitArray

    @classmethod
    def tearDownClass(cls):
        helper.terminate_litematica_jvm()

    def setUp(self):
        pass

    def test_import_from_litematica(self):
        nbits = 6
        size = 33
        jarr = self.JLitematicaBitArray(nbits, size)
        for i in range(size):
            jarr.setAt(i, i)
        longarr = jarr.getBackingLongArray()
        parr = storage.LitematicaBitArray.fromnbtlongarray(longarr, size, nbits)
        for i in range(size):
            self.assertEqual(parr[i], i)

    def test_export_to_litematica(self):
        nbits = 6
        size = 33
        parr = storage.LitematicaBitArray(size, nbits)
        for i in range(size):
            parr[i] = i
        plongs = parr._tolonglist()
        jlongs = self.gateway.new_array(self.gateway.jvm.long, len(plongs))
        for i, l in enumerate(plongs):
            jlongs[i] = l
        jarr = self.JLitematicaBitArray(nbits, size, jlongs)
        for i in range(len(parr)):
            self.assertEqual(parr[i], jarr.getAt(i))
