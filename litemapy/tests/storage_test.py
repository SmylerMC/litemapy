import unittest
import litemapy.storage as storage
import math
from . import helper

class TestLitematicaBitArray(unittest.TestCase):

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
