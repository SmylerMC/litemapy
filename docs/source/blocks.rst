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

.. autoclass:: litemapy.BlockState
    :members:
