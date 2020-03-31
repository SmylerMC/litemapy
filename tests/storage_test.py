import unittest
import litemapy.storage as storage
import math
import tests.helper as helper

class TestLitematicaBitArray(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        helper.setup_litematica()
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

    def test_write_read(self):
        l = [0, 0, 0, 12, 13, 0, 4, 0, 2, 4, 1, 3, 3, 7, 65, 9]
        nbits = math.ceil(math.log(max(l), 2)) + 1
        arr = storage.LitematicaBitArray(len(l), nbits)
        for i, e in enumerate(l):
            arr[i] = e
        for i, e in enumerate(l):
            self.assertEqual(e, arr[i])

    def test_exceptions(self):
        arr = storage.LitematicaBitArray(10, 4)
        def setat(i):
            arr[i] = 0
        def setval(v):
            arr[0] = v
        self.assertRaises(IndexError, setat, -1)
        self.assertRaises(IndexError, setat, 10)
        self.assertRaises(ValueError, setval, -1)
        self.assertRaises(ValueError, setval, 16)

    def test_in(self):
        l = [0, 0, 0, 12, 13, 0, 4, 0, 2, 4, 1, 3, 3, 7, 65, 9]
        nbits = math.ceil(math.log(max(l), 2)) + 1
        arr = storage.LitematicaBitArray(len(l), nbits)
        for i, e in enumerate(l):
            arr[i] = e
        self.assertIn(13, arr)
        self.assertNotIn(15, arr)
