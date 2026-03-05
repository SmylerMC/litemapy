The BlockState class
====================

Blocks in the schematic are represented by the :class:`BlockState` class.
It has a block identifier and block properties.
E.g.

.. code-block:: python

    >>> block = BlockState("minecraft:oak_log", facing="up")
    >>> block.id
    "minecraft:oak_log"
    >>> block["facing"]
    "up"
    >>> "facing" in block
    True

Block states can also carry a :class:`TileEntity` for blocks like chests or hoppers.
When reading from a region, the tile entity is automatically attached:

.. code-block:: python

    >>> chest = region[x, y, z]
    >>> chest.tile_entity
    <TileEntity at (x, y, z)>

When writing to a region, the tile entity is automatically stored:

.. code-block:: python

    >>> from litemapy import BlockState, TileEntity
    >>> from nbtlib.tag import Compound, String
    >>> te = TileEntity(Compound({"id": String("minecraft:chest")}))
    >>> chest = BlockState("minecraft:chest").with_tile_entity(te)
    >>> region[x, y, z] = chest

.. autoclass:: litemapy.BlockState
    :members:
