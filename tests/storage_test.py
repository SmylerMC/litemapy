import unittest
import litemapy.storage as storage
import tests.helper as helper

LITEMATICA_URL = "https://www.curseforge.com/minecraft/mc-mods/litematica/download/2893431/file"
LITEMATICA_FNAME = "litematica.jar"

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

    def test_reading(self):
        arr = self.JLitematicaBitArray(6, 32)
        arr.setAt(0, 3)
        print(arr.getAt(0))

    def test_writing(self):
        print("Testing :)")
