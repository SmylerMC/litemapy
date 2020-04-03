#!/usr/bin/env python3

from litemapy import Schematic, Region, BlockState


# Creating a schematic object and attaching it a region
schem = Schematic(21, 21, 21, name="Planet", author="SmylerMC", description="Made with litemapy", main_region_name="planet")
reg = schem.regions["planet"]

# Create the block state we are going to use (this is mutable)
block = BlockState("minecraft:light_blue_concrete")

# Build the planet
for x in range(21):
    for y in range(21):
        for z in range(21):
            if round(((x-10)**2 + (y-10)**2 + (z-10)**2)**.5) <= 10:
                reg.setblock(x, y, z, block)

# Save the schematic
schem.save("planet.litematic")

# Load the schematic and get its first region
schem = Schematic.load("planet.litematic")
reg = list(schem.regions.values())[0]

# Get the range where to loop, width, height and length
# could be negative depending on the orientation of the build
xran = [reg.width, 0]
xran.sort()
yran = [reg.height, 0]
yran.sort()
zran = [reg.length, 0]
zran.sort()
sx, ex = xran
sy, ey = yran
sz, ez = zran

# Print out the basic shape
for x in range(sx, ex):
    for z in range(sz, ez):
        b = reg.getblock(x, 10, z)
        if b.blockid == "minecraft:air":
            print(" ", end="")
        else:
            print("#", end='')
    print()


