# Litemapy
Litemapy's goal is to provide an easy to use way to read and edit Litematica's schematic file format in python.
[Litematica](https://github.com/maruohon/litematica) is Minecraft mod by maruohon.


## Example
Here is a basic example of creating a schematic, and of reading one:
```python
from litemapy import Schematic, Region, BlockState

# Creating a schematic object and attaching it a region
schem = Schematic(name="Planet", author="SmylerMC", description="Made with litemapy")
reg = schem.regions.setdefault("planet", default=Region(0, 0, 0, 21, 21, 21))

# Create the block state we are going to use (this is mutable)
block = BlockState("minecraft:light_blue_concrete")

# Build the planet
for x, y, z in reg.allblockpos(): # Iterates over all coordinates in this region
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
  * Preview screenshots are not supported
  * Legacy Schematica schematics are not supported at all, only the newer Litematica format is

## Dependencies
The only direct dependency is [nbtlib](https://github.com/vberlier/nbtlib), which is available on pypi and should be installed automatically when using pip.

However, if you wish to play around with the code, please not that the test suite compares Litemapy's behavior with Litematica's to make sure it matches, and therefore needs a valid JDK installation and [Py4J](https://www.py4j.org/index.html). Tose specific tests have only been tested on POSIX systems.
