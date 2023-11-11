from litemapy import Schematic, Region, BlockState
from os import walk, path
from constants import *
import helper
from tempfile import TemporaryDirectory

valid_files = []
for directory, child_directory, file_names in walk(VALID_LITEMATIC_DIRECTORY):
    for file_name in file_names:
        valid_files.append(path.join(directory, file_name))


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
        file_path = path.join(temporary_directory.name, write_schematic.name + ".litematic")
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


def test_region_filter():
    def do_filter(before_schematic, after_schematic, function):
        print(f"Comparing litematic files {before_schematic} and {after_schematic}")
        before_schematic = path.join(FILTER_LITEMATIC_DIRECTORY, before_schematic)
        after_schematic = path.join(FILTER_LITEMATIC_DIRECTORY, after_schematic)
        before_schematic = Schematic.load(before_schematic)
        after_schematic = Schematic.load(after_schematic)
        assert len(before_schematic.regions) == 1, "Invalid test litematic"
        assert len(after_schematic.regions) == 1, "Invalid test litematic"
        (before_schematic,) = before_schematic.regions.values()
        (after_schematic,) = after_schematic.regions.values()
        assert before_schematic.width == after_schematic.width, "Invalid test litematic"
        assert before_schematic.height == after_schematic.height, "Invalid test litematic"
        assert before_schematic.length == after_schematic.length, "Invalid test litematic"
        before_schematic.filter(function)
        for x in before_schematic.xrange():
            for y in before_schematic.yrange():
                for z in before_schematic.zrange():
                    state_1 = before_schematic.getblock(x, y, z)
                    state_2 = after_schematic.getblock(x, y, z)
                    assert state_1 == state_2

    def all_blue_filter(b: BlockState):
        return BlockState("minecraft:light_blue_concrete")

    do_filter('rainbow-line.litematic', 'blue-line.litematic', all_blue_filter)

    red = BlockState("minecraft:red_concrete")
    blue = BlockState("minecraft:blue_concrete")

    def black_red_white_blue(b: BlockState):
        if b.blockid == "minecraft:black_concrete":
            return red
        if b.blockid == "minecraft:white_concrete":
            return blue
        return b

    do_filter('black-white.litematic', 'red-blue.litematic', black_red_white_blue)

    def glassify(state: BlockState):
        if "water" in state.blockid:
            return BlockState("minecraft:blue_stained_glass")
        elif state.blockid == "minecraft:sand":
            return BlockState('minecraft:yellow_stained_glass')
        elif state.blockid == "minecraft:dirt":
            return BlockState("minecraft:brown_stained_glass")
        elif state.blockid == "minecraft:stone":
            return BlockState("minecraft:light_gray_stained_glass")
        elif state.blockid in ("minecraft:grass_block", "minecraft:birch_leaves"):
            return BlockState("minecraft:green_stained_glass")
        elif state.blockid == "minecraft:birch_log":
            return BlockState("minecraft:white_stained_glass")
        elif state.blockid == "minecraft:copper_ore":
            return BlockState("minecraft:orange_stained_glass")
        elif state.blockid == "minecraft:grass":
            return BlockState("minecraft:green_stained_glass_pane", east="true", north="true", south="true",
                              west="true", waterlogged="false")
        return state

    do_filter('tree.litematic', 'tree-glass.litematic', glassify)

    def wool_to_concrete(b: BlockState):
        return b.with_blockid(b.blockid.replace('wool', 'concrete'))

    do_filter('concrete-wool.litematic', 'concrete-full.litematic', wool_to_concrete)
