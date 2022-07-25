<div align="center">
<h1>Litemapy</h1>
Litemapy's goal is to provide an easy to use way to read and edit Litematica's schematic file format in python.
<a href="https://github.com/maruohon/litematica">Litematica</a> is Minecraft mod by maruohon.


![PyPI - Python Version](https://img.shields.io/pypi/pyversions/litemapy?style=flat-square)
![PyPI](https://img.shields.io/pypi/v/litemapy?style=flat-square)
![PyPI - Downloads](https://img.shields.io/pypi/dm/litemapy?style=flat-square)
![Commits since latest release](https://img.shields.io/github/commits-since/SmylerMC/litemapy/latest?include_prereleases&style=flat-square)
[![Documentation Status](https://readthedocs.org/projects/litemapy/badge/?version=latest)](https://litemapy.readthedocs.io/en/latest/?badge=latest&style=flat-square)
</div>

## Installation
Litemapy is available on pypi:
```bash
pip install litemapy
```

## Features:
  * Read and write .litematic files
  * Full support for litematics' regions concept
  * Full block storage support
  * Full support for basic metadata handling (author, name, description, block count and total volume)
  * Partial support for entities
  * Partial support for tile entities
  * Partial support for pending block updates
  * Partial support for preview images

## Documentation
Documentation is available on ReadTheDocs: [litemapy.rtfd.io](https://litemapy.rtfd.io).
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