#!/usr/bin/env python3

from litemapy import Schematic, Region, BlockState

# Shortcut to create a schematic with a single region
reg = Region(0, 0, 0, 21, 21, 21)
schem = reg.as_schematic(name="Planet", author="SmylerMC", description="Made with litemapy")

# Create the block state we are going to use
block = BlockState("minecraft:light_blue_concrete")

# Build the planet
for x, y, z in reg.block_positions():
    if round(((x - 10) ** 2 + (y - 10) ** 2 + (z - 10) ** 2) ** .5) <= 10:
        reg[x, y, z] = block

# Save the schematic
schem.save("planet.litematic")

# Load the schematic and get its first region
schem = Schematic.load("planet.litematic")
reg = list(schem.regions.values())[0]

# Print out the basic shape
for x in reg.range_x():
    for z in reg.range_z():
        b = reg[x, 10, z]
        if b.id == "minecraft:air":
            print(" ", end="")
        else:
            print("#", end='')
    print()
