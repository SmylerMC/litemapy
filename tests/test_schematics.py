from litemapy import Schematic, Region, BlockState
from os import walk
from constants import *
import helper
from tempfile import TemporaryDirectory


valid_files = []
for directory, child_directory, file_names in walk(VALID_LITEMATIC_DIRECTORY):
    for file_name in file_names:
        valid_files.append(directory + "/" + file_name)


def test_valid_litematics_do_not_raise_exception_when_loaded():
    for file_path in valid_files:
        Schematic.load(file_path)


def test_regions_have_accurate_sizes():
    sch = Schematic()
    assert sch.width == 0
    assert sch.height == 0
    assert sch.length == 0
    reg1 = Region(0, 0, 0, 10, 10, 10)
    reg2 = Region(90, 0, 0, 10, 10, 10)
    reg3 = Region(50, 0, 0, 10, 10, 10)
    reg4 = Region(49, 0, 0, -10, 10, 10)
    sch.regions["a"] = reg1
    assert sch.width == 10
    assert sch.height == 10
    assert sch.length == 10
    sch.regions["b"] = reg2
    assert sch.width == 100
    sch.regions["c"] = reg3
    assert sch.width == 100
    del sch.regions["b"]
    assert sch.width == 60
    sch.regions["c"] = reg4
    assert sch.width == 50


def test_region_min_and_max_are_accurate():
    reg = Region(0, 0, 0, 10, 20, 30)
    assert reg.minschemx() == 0
    assert reg.maxschemx() == 9
    assert reg.minschemy() == 0
    assert reg.maxschemy() == 19
    assert reg.minschemz() == 0
    assert reg.maxschemz() == 29
    assert reg.minx() == 0
    assert reg.maxx() == 9
    assert reg.miny() == 0
    assert reg.maxy() == 19
    assert reg.minz() == 0
    assert reg.maxz() == 29
    reg = Region(0, 0, 0, -10, -20, -30)
    assert reg.minschemx() == -9
    assert reg.maxschemx() == 0
    assert reg.minschemy() == -19
    assert reg.maxschemy() == 0
    assert reg.minschemz() == -29
    assert reg.maxschemz() == 0
    assert reg.minx() == -9
    assert reg.maxx() == 0
    assert reg.miny() == -19
    assert reg.maxy() == 0
    assert reg.minz() == -29
    assert reg.maxz() == 0
    reg = Region(10, 10, 10, 10, 10, 10)
    assert reg.minschemx() == 10
    assert reg.maxschemx() == 19
    assert reg.minschemy() == 10
    assert reg.maxschemy() == 19
    assert reg.minschemz() == 10
    assert reg.maxschemz() == 19
    assert reg.minx() == 0
    assert reg.maxx() == 9
    assert reg.miny() == 0
    assert reg.maxy() == 9
    assert reg.minz() == 0
    assert reg.maxz() == 9
    reg = Region(-10, -10, -10, 10, 10, 10)
    assert reg.minschemx() == -10
    assert reg.maxschemx() == -1
    assert reg.minschemy() == -10
    assert reg.maxschemy() == -1
    assert reg.minschemz() == -10
    assert reg.maxschemz() == -1
    assert reg.minx() == 0
    assert reg.maxx() == 9
    assert reg.miny() == 0
    assert reg.maxy() == 9
    assert reg.minz() == 0
    assert reg.maxz() == 9
    reg = Region(-10, -10, -10, -10, -10, -10)
    assert reg.minschemx() == -19
    assert reg.maxschemx() == -10
    assert reg.minschemy() == -19
    assert reg.maxschemy() == -10
    assert reg.minschemz() == -19
    assert reg.maxschemz() == -10
    assert reg.minx() == -9
    assert reg.maxx() == 0
    assert reg.miny() == -9
    assert reg.maxy() == 0
    assert reg.minz() == -9
    assert reg.maxz() == 0


def test_are_random_schematics_preserved_when_reading_and_writing():
    temporary_directory = TemporaryDirectory()
    for i in range(100):
        write_schematic = helper.randomschematic()
        file_path = temporary_directory.name + "/" + write_schematic.name + ".litematic"
        write_schematic.save(file_path)
        read_schematic = Schematic.load(file_path)

        # Assert metadata is equals
        assert write_schematic.name == read_schematic.name
        assert write_schematic.author == read_schematic.author
        assert write_schematic.description == read_schematic.description
        assert write_schematic.width == read_schematic.width
        assert write_schematic.height == read_schematic.height
        assert write_schematic.length == read_schematic.length
        assert len(write_schematic.regions) == len(read_schematic.regions)
        for name, write_region in write_schematic.regions.items():
            read_region = read_schematic.regions[name]

            # Assert computed values are equal
            assert write_region.minx() == read_region.minx()
            assert write_region.maxx() == read_region.maxx()
            assert write_region.miny() == read_region.miny()
            assert write_region.maxy() == read_region.maxy()
            assert write_region.minz() == read_region.minz()
            assert write_region.maxz() == read_region.maxz()
            assert write_region.minschemx() == read_region.minschemx()
            assert write_region.maxschemx() == read_region.maxschemx()
            assert write_region.minschemy() == read_region.minschemy()
            assert write_region.maxschemy() == read_region.maxschemy()
            assert write_region.minschemz() == read_region.minschemz()
            assert write_region.maxschemz() == read_region.maxschemz()

            # Assert all blocks are equal
            for x, y, z in write_region.allblockpos():
                ws = write_region.getblock(x, y, z)
                rs = read_region.getblock(x, y, z)
                assert ws == rs

    temporary_directory.cleanup()


def test_blockstate():
    # TODO Split into multiple smaller tests
    prop = {"test1": "testval", "test2": "testval2"}
    b = BlockState("minecraft:stone", properties=prop)
    assert len(prop) == len(b)
    for k, v in prop.items():
        assert b[k] == v
    nbt = b._tonbt()
    b2 = BlockState.fromnbt(nbt)
    assert b == b2
