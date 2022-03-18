# Litemapy
Litemapy's goal is to provide an easy to use way to read and edit Litematica's schematic file format in python.
[Litematica](https://github.com/maruohon/litematica) is Minecraft mod by maruohon.


![PyPI - Python Version](https://img.shields.io/pypi/pyversions/litemapy?style=flat-square)
![PyPI](https://img.shields.io/pypi/v/litemapy?style=flat-square)
![Commits since latest release](https://img.shields.io/github/commits-since/SmylerMC/litemapy/latest?include_prereleases&style=flat-square)


## Example
Here is a basic example of creating a schematic, and of reading one:
```python
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
```
When ran, we get the expected output:
```
       #######       
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
  * Entities are partially supported.
  * Tile entities are partially supported.
  * Pending block updates are not supported, but retained when reading and saving.
  * Legacy Schematica schematics are not supported at all, only the newer Litematica format is.

## Documentation
Sadly, documentation is yet to be written.

## Dependencies
The only direct dependency is [nbtlib](https://github.com/vberlier/nbtlib), which is available on pypi and should install automatically with pip.

However, if you wish to play around with the code, please not that the test suite compares Litemapy's behavior with Litematica's to make sure it matches, and therefore needs a valid JDK installation and [Py4J](https://www.py4j.org/index.html). Those specific tests have only been tested on POSIX systems.
