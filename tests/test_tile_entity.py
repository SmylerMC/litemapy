from tempfile import TemporaryDirectory
from os import path

from litemapy import Schematic, Region, BlockState, TileEntity
from nbtlib.tag import Compound, String, List, Byte


def test_tile_entity_copy_on_assignment():
    reg_a = Region(0, 0, 0, 5, 5, 5)
    pos_a = (1, 1, 1)

    te_nbt = Compound({
        "id": String("minecraft:hopper"),
        "Items": List[Compound]([
            Compound({
                "Slot": Byte(0),
                "id": String("minecraft:diamond"),
                "Count": Byte(1)
            })
        ])
    })
    te = TileEntity(te_nbt)

    hopper = BlockState("minecraft:hopper").with_tile_entity(te)
    reg_a[pos_a] = hopper

    retrieved_a = reg_a[pos_a]
    assert retrieved_a.id == "minecraft:hopper"
    assert retrieved_a.tile_entity is not None
    assert retrieved_a.tile_entity.data["Items"][0]["id"] == "minecraft:diamond"

    reg_b = Region(0, 0, 0, 10, 10, 10)
    pos_b = (5, 5, 5)

    reg_b[pos_b] = reg_a[pos_a]

    retrieved_b = reg_b[pos_b]
    assert retrieved_b.id == "minecraft:hopper"
    assert retrieved_b.tile_entity is not None
    assert retrieved_b.tile_entity.data["Items"][0]["id"] == "minecraft:diamond"
    assert retrieved_b.tile_entity.position == pos_b
    assert int(retrieved_b.tile_entity.data["x"]) == pos_b[0]

    # Verify deep copy
    reg_a[pos_a].tile_entity.data["Items"][0]["id"] = String("minecraft:dirt")
    assert reg_b[pos_b].tile_entity.data["Items"][0]["id"] == "minecraft:diamond"


def test_tile_entity_removal_on_overwrite():
    reg = Region(0, 0, 0, 3, 3, 3)
    pos = (1, 1, 1)

    te = TileEntity(Compound({"id": String("minecraft:hopper")}))
    reg[pos] = BlockState("minecraft:hopper").with_tile_entity(te)
    assert len(reg.tile_entities) == 1

    reg[pos] = BlockState("minecraft:air")

    assert len(reg.tile_entities) == 0
    assert reg[pos].tile_entity is None


def test_tile_entity_overwrite_with_another_tile_entity():
    reg = Region(0, 0, 0, 3, 3, 3)
    pos = (1, 1, 1)

    te_diamond = TileEntity(Compound({
        "id": String("minecraft:chest"),
        "Items": List[Compound]([
            Compound({"Slot": Byte(0), "id": String("minecraft:diamond"), "Count": Byte(1)})
        ])
    }))
    reg[pos] = BlockState("minecraft:chest").with_tile_entity(te_diamond)
    assert reg[pos].tile_entity.data["Items"][0]["id"] == "minecraft:diamond"

    te_emerald = TileEntity(Compound({
        "id": String("minecraft:chest"),
        "Items": List[Compound]([
            Compound({"Slot": Byte(0), "id": String("minecraft:emerald"), "Count": Byte(1)})
        ])
    }))
    reg[pos] = BlockState("minecraft:chest").with_tile_entity(te_emerald)

    # Old tile entity should be replaced, not accumulated
    assert len(reg.tile_entities) == 1
    assert reg[pos].tile_entity.data["Items"][0]["id"] == "minecraft:emerald"


def test_get_tile_entity_returns_none_for_empty_position():
    reg = Region(0, 0, 0, 3, 3, 3)
    assert reg.get_tile_entity((0, 0, 0)) is None
    assert reg[0, 0, 0].tile_entity is None


def test_with_id_preserves_tile_entity():
    te = TileEntity(Compound({
        "id": String("minecraft:chest"),
        "Items": List[Compound]([
            Compound({"Slot": Byte(0), "id": String("minecraft:diamond"), "Count": Byte(1)})
        ])
    }))
    chest = BlockState("minecraft:chest").with_tile_entity(te)
    barrel = chest.with_id("minecraft:barrel")
    assert barrel.id == "minecraft:barrel"
    assert barrel.tile_entity is not None
    assert barrel.tile_entity.data["Items"][0]["id"] == "minecraft:diamond"


def test_with_properties_preserves_tile_entity():
    te = TileEntity(Compound({"id": String("minecraft:chest")}))
    chest = BlockState("minecraft:chest", facing="north").with_tile_entity(te)
    updated = chest.with_properties(facing="south")
    assert updated["facing"] == "south"
    assert updated.tile_entity is not None


def test_litematic_round_trip_preserves_tile_entities():
    reg = Region(0, 0, 0, 5, 5, 5)

    te_1 = TileEntity(Compound({
        "id": String("minecraft:chest"),
        "Items": List[Compound]([
            Compound({"Slot": Byte(0), "id": String("minecraft:diamond"), "Count": Byte(64)})
        ])
    }))
    reg[1, 1, 1] = BlockState("minecraft:chest").with_tile_entity(te_1)

    te_2 = TileEntity(Compound({
        "id": String("minecraft:chest"),
        "Items": List[Compound]([
            Compound({"Slot": Byte(0), "id": String("minecraft:emerald"), "Count": Byte(16)})
        ])
    }))
    reg[3, 2, 1] = BlockState("minecraft:chest").with_tile_entity(te_2)

    reg[0, 0, 0] = BlockState("minecraft:stone")

    schem = Schematic(name="te_test", author="test", description="test", regions={"main": reg})

    with TemporaryDirectory() as tmp:
        file_path = path.join(tmp, "te_test.litematic")
        schem.save(file_path)
        loaded = Schematic.load(file_path)

    loaded_reg = loaded.regions["main"]
    assert len(loaded_reg.tile_entities) == 2

    b1 = loaded_reg[1, 1, 1]
    assert b1.id == "minecraft:chest"
    assert b1.tile_entity is not None
    assert b1.tile_entity.data["Items"][0]["id"] == "minecraft:diamond"
    assert int(b1.tile_entity.data["Items"][0]["Count"]) == 64

    b2 = loaded_reg[3, 2, 1]
    assert b2.id == "minecraft:chest"
    assert b2.tile_entity is not None
    assert b2.tile_entity.data["Items"][0]["id"] == "minecraft:emerald"

    # Blocks without tile entities should not be affected
    assert loaded_reg[0, 0, 0].tile_entity is None
    assert loaded_reg[0, 0, 0].id == "minecraft:stone"
