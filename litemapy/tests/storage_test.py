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

class TestDiscriminatingDictionnary(unittest.TestCase):

    def test_basic_set_get(self):
        def discri(k, v):
            print("Discriminating ", type(k), k, "=>", type(v), v)
            return v >= 0, "Need pos"
        posdi = storage.DiscriminatingDictionnary(discri)
        posdi["0"] = 0
        self.assertTrue(posdi["0"] == 0)
        self.assertTrue("0" in posdi)
        self.assertTrue("0" in posdi.keys())
        self.assertTrue(0 in posdi.values())
        self.assertIsNone(posdi.get("1"))
        def seti(i, v):
            posdi[i] = v
        self.assertRaises(storage.DiscriminationError, seti, '-1', -1)
        otherdir = {"1": 1, "2": 2}
        posdi.update(otherdir)
        self.assertTrue("1" in posdi)
        self.assertTrue("2" in posdi)
        self.assertRaises(storage.DiscriminationError, posdi.update, {"-1": -1})
        otherdir = {"1": 1, "2": 2}
        posdi = storage.DiscriminatingDictionnary(lambda k, v: (v>=0, "Need pos"), otherdir)
        self.assertTrue("1" in posdi)
        self.assertTrue("2" in posdi)
        posdi = storage.DiscriminatingDictionnary(lambda k, v: (v>=0, "Need pos"), a=1, b=2)
        self.assertTrue("a" in posdi)
        self.assertTrue("b" in posdi)

    def test_onadd(self):
        class Counter:
            def __init__(self):
                self.counter = 0
            def onadd(self, k, v):
                self.counter += v
        c = Counter()
        posdi = storage.DiscriminatingDictionnary(
                lambda k, v: (v>=0, "Need pos"),
                onadd=c.onadd,
                x=10
        )
        posdi["a"] = 1
        self.assertEqual(c.counter, 1)
        posdi.update({"b": 2, "c": 3})
        self.assertEqual(c.counter, 6)
        posdi.setdefault("d", 4)
        self.assertEqual(c.counter, 10)

    def test_onremove(self):
        class Counter:
            def __init__(self):
                self.counter = 0
            def onrm(self, k, v):
                self.counter += v
        c = Counter()
        posdi = storage.DiscriminatingDictionnary(
                lambda k, v: (v>=0, "Need pos"),
                onremove=c.onrm,
                a=1, b=2, c=3, d=4, x=10
        )
        del posdi["a"]
        self.assertEqual(c.counter, 1)
        posdi.pop("b")
        self.assertEqual(c.counter, 3)
        posdi.pop("c")
        self.assertEqual(c.counter, 6)
        posdi.pop("d")
        self.assertEqual(c.counter, 10)
        posdi.popitem()
        self.assertEqual(c.counter, 20)
        c = Counter()
        posdi = storage.DiscriminatingDictionnary(
                lambda k, v: (v>=0, "Need pos"),
                onremove=c.onrm,
                a=1, b=2, c=3, d=4, x=10
        )
        posdi.clear()
        self.assertEqual(c.counter, 20)

    def test_onadd_onremove(self):
        class Counter:
            def __init__(self):
                self.added = 0
                self.removed = 0
            def onrm(self, k, v):
                self.removed += v
            def onadd(self, k, v):
                self.added += v
        c = Counter()
        posdi = storage.DiscriminatingDictionnary(
                lambda k, v: (v>=0, "Need pos"),
                onadd=c.onadd,
                onremove=c.onrm,
                a=1, b=2, c=3, d=4, x=10
        )
        posdi["c"] = 7
        self.assertEqual(c.added, 7)
        self.assertEqual(c.removed, 3)
        posdi.update({"x": 100, "d": 500, "y": 200})
        self.assertEqual(c.added, 807)
        self.assertEqual(c.removed, 17)

