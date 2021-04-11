#!/usr/bin/env python3

from litemapy import Schematic, Region, BlockState


# Creating a schematic object and attaching it a region
schem = Schematic(name="Planet", author="SmylerMC", description="Made with litemapy")
reg = schem.regions.setdefault("planet", default=Region(0, 0, 0, 21, 21, 21))

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


