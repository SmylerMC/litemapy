Getting started
===============

Litemapy is `available on PyPi <https://https://pypi.org/project/litemapy/>`_ can therefore be installed with pip:

.. code-block:: sh

    pip install litemapy

Litemapy itself is not complicated, but Litematica is quite powerful
and its file format is therefore not as simple as other similar schematic file formats,
so make sure to read the :doc:`Litematic page <litematics>` if you feel like something is unclear about the format
or how it plays with Litemapy.

.. code-block:: python
    :caption: Because it is worth a thousand words, here is a simple example:

    from litemapy import Schematic, Region, BlockState

    # Shortcut to create a schematic with a single region
    reg = Region(0, 0, 0, 21, 21, 21)
    schem = reg.as_schematic(name="Planet", author="SmylerMC", description="Made with litemapy")

    # Create the block state we are going to use
    block = BlockState("minecraft:light_blue_concrete")

    # Build the planet
    for x, y, z in reg.allblockpos():
        if round(((x-10)**2 + (y-10)**2 + (z-10)**2)**.5) <= 10:
            reg.setblock(x, y, z, block)

    # Save the schematic
    schem.save("planet.litematic")

    # Load the schematic and get its first region
    schem = Schematic.load("planet.litematic")
    reg = list(schem.regions.values())[0]

    # Print out the basic shape
    for x in reg.xrange():
        for z in reg.zrange():
            b = reg.getblock(x, 10, z)
            if b.blockid == "minecraft:air":
                print(" ", end="")
            else:
                print("#", end='')
        print()
