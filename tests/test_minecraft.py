from litemapy import BlockState


def test_blockstate_initialization():
    # TODO Split into multiple smaller tests
    prop = {"test1": "testval", "test2": "testval2"}
    b = BlockState("minecraft:stone", **prop)
    assert len(prop) == len(b)
    for k, v in prop.items():
        assert b[k] == v


def test_blockstate_nbt_is_identity():
    prop = {"test1": "testval", "test2": "testval2"}
    blockstate_1 = BlockState("minecraft:stone", **prop)
    nbt = blockstate_1.to_nbt()
    blockstate_2 = BlockState.fromnbt(nbt)
    assert blockstate_1 == blockstate_2


def test_blockstate_with_properties():
    prop = {"test1": "testval1", "test2": "testval2"}
    blockstate_1 = BlockState("minecraft:stone", **prop)
    blockstate_2 = blockstate_1.with_properties(test3="testval3", test4="testval4")
    assert blockstate_2.to_block_state_identifier() == "minecraft:stone[test1=testval1,test2=testval2,test3=testval3,test4=testval4]"

    blockstate_3 = blockstate_2.with_properties(test4=None)
    assert blockstate_3.to_block_state_identifier() == "minecraft:stone[test1=testval1,test2=testval2,test3=testval3]"
