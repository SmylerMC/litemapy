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
	
