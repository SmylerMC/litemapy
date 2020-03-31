# Litemapy
Litemapy's goal is to provide an easy to use way to read and edit Litematica's schematic file format in python.
[Litematica](https://github.com/maruohon/litematica) is Minecraft mod by maruohon.


## Example
Here is a basic example of creating a schematic, and of reading one:
```
from litemapy.schematic import Schematic, Region, BlockState


# Creating a schematic object and attaching it a region
schem = Schematic(21, 21, 21, name="Planet", author="SmylerMC", description="Made with litemapy")
reg = Region(0, 0, 0, 21, 21, 21, name="planet")
schem.regions.append(reg)

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
reg = schem.regions[0]

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
```
When ran, we get the expected output:
```       #######       
     ###########     
    #############    
   ###############   
  #################  
 ################### 
 ################### 
#####################
#####################
#####################
#####################
#####################
#####################
#####################
 ################### 
 ################### 
  #################  
   ###############   
    #############    
     ###########     
       #######
```

## Installation
Litemapy is available on pypi: ```pip install litemapy```

## Content
Litemapy is still new and only has basic functionalities, it lacks support for some of Litematica's, notably:
  * Entities are not supported
  * Tile entities are not supported
  * Pending block updates are not supported
  * Legacy Schematica schematics are not supported at all, only the newer Litematica format is

## Dependencies
The only direct dependency is [nbtlib](https://github.com/vberlier/nbtlib), which is available on pypi and should be installed automatically when using pip.

However, if you wish to play around with the code, please not that the test suite compares Litemapy's behavior with Litematica's to make sure it matches, and therefore needs [GitPython](https://github.com/gitpython-developers/GitPython) to clone Litematica's repo, a valid JDK installation to compile litematica, and [Py4J](https://www.py4j.org/index.html) to create a gateway between the JVM and Python. The test suite currently only runs on POSIX systems.
