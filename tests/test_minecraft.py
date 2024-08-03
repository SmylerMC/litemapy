import pytest

from litemapy import BlockState
from litemapy.minecraft import is_valid_identifier
from litemapy.minecraft import InvalidIdentifier
from litemapy.schematic import AIR


def test_blockstate_initialization():
    prop = {"test1": "testval", "test2": "testval2"}
    b = BlockState("minecraft:stone", **prop)
    assert len(prop) == len(b)
    for k, v in prop.items():
        assert b[k] == v


def test_cannot_create_blockstate_with_invalid_id():
    ids = (
        "",
        "minecraft stone",
        "stone",
        "minecraft:stone[property=value]",
    )
    for id_ in ids:
        with pytest.raises(InvalidIdentifier):
            BlockState(id_, prop="val")
        with pytest.raises(InvalidIdentifier):
            AIR.with_id(id_)


def test_blockstate_nbt_is_identity():
    prop = {"test1": "testval", "test2": "testval2"}
    blockstate_1 = BlockState("minecraft:stone", **prop)
    nbt = blockstate_1.to_nbt()
    blockstate_2 = BlockState.from_nbt(nbt)
    assert blockstate_1 == blockstate_2


def test_blockstate_with_properties():
    prop = {"test1": "testval1", "test2": "testval2"}
    blockstate_1 = BlockState("minecraft:stone", **prop)
    blockstate_2 = blockstate_1.with_properties(test3="testval3", test4="testval4")
    assert blockstate_2.to_block_state_identifier() == "minecraft:stone[test1=testval1,test2=testval2,test3=testval3,test4=testval4]"

    blockstate_3 = blockstate_2.with_properties(test4=None)
    assert blockstate_3.to_block_state_identifier() == "minecraft:stone[test1=testval1,test2=testval2,test3=testval3]"


def test_blockstate_is_hashable():
    state1 = BlockState("minecraft:air")
    state2 = BlockState("minecraft:air")
    assert state1 == state2
    assert hash(state1) == hash(state2)
    assert hash(state1) == hash(state1)


def test_is_valid_identifier():
    assert is_valid_identifier("minecraft:air")
    assert is_valid_identifier("minecraft:stone_cutter")
    assert is_valid_identifier("terramap:path/is/allowed_slashes.png")
    assert is_valid_identifier("weird.mod-id:both_are_allowed-dashes-and_underscores.and.dots")

    assert not is_valid_identifier("")
    assert not is_valid_identifier(" ")
    assert not is_valid_identifier("minecraft:minecraft:stone")
    assert not is_valid_identifier("minecraft:oak_stairs[facing=north]")
    assert not is_valid_identifier("minecraft")
