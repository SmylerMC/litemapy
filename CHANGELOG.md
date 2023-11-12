### 0.8.0b0
* Breaking change: the `BlockState` constructor no longer takes properties as a single `properties` argument.
Each property must be supplied as its own keyword argument instead.
E.g. `BlockState("minecraft:acacia_log", facing="west")`
* Added `BlockState.with_properties()` and `BlockState.with_blockid()` to create copies of block states
but with different ids and properties.
* Added `Region.filter()` to allow for efficient block replacement.
* Schematic palettes are now always optimized before saving

### 0.7.0b0:
* Method to convert regions to the sponge schematic NBT format
* Fix crash with litematics created by newer versions of Litematica "id -> The required key is missing in the (Tile)Entity's NBT Compound",
It was caused by Litematica no longer specifying a TileEntity's ID in its own NBT structure
(it can be assumed by looking the block at the TileEntity's coordinates)
* Made internal list fields access only (Region#entities, Region#tile_entities, Region#block_ticks, Region#fluid_ticks)

### 0.6.0b0:
* Method to convert regions to the vanilla Minecraft structure NBT format

### 0.5.0b0:
* Basic support for entities
* Basic support for tile entities
* Basic support for preview images
* Retain block and fluid pending ticks when reading and then saving a litematic

### 0.4.1a0:
* Uses nbtlib versions above 2.0.3, older 2.0.X versions are broken.

### 0.4.0a0:
*  Support for nbtlib 2.0
*  Drop support for python 3.7

#### 0.3.1a0:
 * Bugfix: Save timestamp as milliseconds instead of seconds

#### 0.3.0a0:
 * Made BlockState immutable.
 * BlockState properties should now be accessed directly from the blockstate instead of from its no longer visible properties field (e.g. `blockstate["propertyname"]` instead of `blockstate.properties["propertyname"]`).
 * Correctly handle multiple regions in a single schematic. Schematic's enclosing sizes are no longer supplied by the user but rather calculated from the schematic's regions.
 * String representation of BlockStates.
 * Helper methods to iterate over region coordinates and get a region extrem coordinates in its schematic.
 * Helper method to create a schematic from a single region.
 * Use numpy for storage.

#### 0.2.1a0:
* Bug fix by @SebbyFur : Properly initialize block state properties
* Refactored tests

#### 0.2.0a0:
* Modification time is now updated when writing a file
* Refactored constants into a separate file
* Added a software metadata to help identify schematics created with litemapy and the version used
* Added a DiscriminatoryDictionnary class to store regions in schematics while making sure they fit in
* Regions are now stored in a read only discriminatory dictionnary of the schematic, using their names as key
* Trying to add a region that does not fit into a schematic raises an error
* Region's names are not stored in region anymore
* Region's positions and sizes are now read only
* Region's palettes are now private
* Schematic's size is now read only

#### 0.1.1a0:
* Refactored package

#### 0.1.0a0:
* Initial alpha release with read/write support
	
