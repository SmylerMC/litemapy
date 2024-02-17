#!/usr/bin/env python3


"""
This file provides an example for how to do mass block replacement with Litemapy, using Region.filter().
While the most straightforward approach would be to simply iterate over the region's coordinates to get and set
each and every block that would be terribly inefficient.

Region.filter() is able to change all blocks of the same tima at once by manipulating the litematic's palette,
which is a lot more efficient (like 10x faster).

Here, we replace all blocks with stained-glass of a similar color.
"""

from litemapy import Schematic, BlockState
from sys import argv
from time import time

# Just a lookup for which blocks will be replaced with which
# Has blocks for a mushroom-island / iceberg area.
LOOKUP: dict[str, BlockState] = {
    'minecraft:air': BlockState("minecraft:air"),
    'minecraft:stone': BlockState("minecraft:light_gray_stained_glass"),
    'minecraft:granite': BlockState("minecraft:orange_stained_glass"),
    'minecraft:diorite': BlockState("minecraft:white_stained_glass"),
    'minecraft:gravel': BlockState("minecraft:gray_stained_glass"),
    'minecraft:dirt': BlockState("minecraft:brown_stained_glass"),
    'minecraft:water': BlockState("minecraft:blue_stained_glass"),
    'minecraft:andesite': BlockState("minecraft:light_gray_stained_glass"),
    'minecraft:sand': BlockState("minecraft:yellow_stained_glass"),
    'minecraft:mycelium': BlockState("minecraft:light_gray_stained_glass"),
    'minecraft:red_mushroom_block': BlockState("minecraft:red_stained_glass"),
    'minecraft:brown_mushroom_block': BlockState("minecraft:brown_stained_glass"),
    'minecraft:mushroom_stem': BlockState("minecraft:white_stained_glass"),
    'minecraft:blue_ice': BlockState("minecraft:light_blue_stained_glass"),
    'minecraft:packed_ice': BlockState("minecraft:light_blue_stained_glass"),
    'minecraft:spruce_stairs': BlockState("minecraft:brown_stained_glass"),
    'minecraft:jungle_stairs': BlockState("minecraft:brown_stained_glass"),
    'minecraft:spruce_fence': BlockState("minecraft:brown_stained_glass"),
    'minecraft:jungle_fence': BlockState("minecraft:brown_stained_glass"),
    'minecraft:glow_lichen': BlockState("minecraft:air"),
    'minecraft:coal_ore': BlockState("minecraft:black_stained_glass"),
    'minecraft:copper_ore': BlockState("minecraft:orange_stained_glass"),
    'minecraft:iron_ore': BlockState("minecraft:white_stained_glass"),
    'minecraft:clay': BlockState("minecraft:light_gray_stained_glass"),
    'minecraft:lapis_ore': BlockState("minecraft:blue_stained_glass"),
    'minecraft:brown_mushroom': BlockState("minecraft:blue_stained_glass_pane"),
    'minecraft:snow_block': BlockState("minecraft:white_stained_glass"),
    'minecraft:raw_copper_block': BlockState("minecraft:orange_stained_glass"),
    'minecraft:bubble_column': BlockState("minecraft:blue_stained_glass"),
    'minecraft:magma_block': BlockState("minecraft:red_stained_glass"),
    'minecraft:spruce_planks': BlockState("minecraft:brown_stained_glass"),
    'minecraft:jungle_planks': BlockState("minecraft:orange_stained_glass"),
    'minecraft:spruce_trapdoor': BlockState("minecraft:brown_stained_glass"),
    'minecraft:chest': BlockState("minecraft:yellow_stained_glass"),
    'minecraft:spruce_log': BlockState("minecraft:brown_stained_glass"),
    'minecraft:grass_block': BlockState("minecraft:green_stained_glass"),
    'minecraft:sugar_cane': BlockState("minecraft:light_green_stained_glass_pane"),
}


# This is the most important function.
# It will be called once by Litemapy for each block type in the schematic.
def glassify(state: BlockState) -> BlockState:
    new_state = LOOKUP.get(state.blockid)
    if new_state is None:
        print(f"Unknown block: {state}")
        return state
    return new_state


def glacify_litematic(in_file: str, out_file: str):
    # Load the schematic and print some metadata
    print(f"Loading {in_file}...")
    litematic = Schematic.load(in_file)
    print(f"Litematic name: {litematic.name}")
    print(f"Litematic description: {litematic.description}")
    print(f"Litematic author: {litematic.author}")

    # Gather some stats
    start = time()
    total_blocks = 0

    # Schematics can contain multiple regions, we need to process them all
    for name, region in litematic.regions.items():
        # Update the stats
        volume = region.getvolume()
        total_blocks += volume
        print(f"Processing region {name} of volume {volume} blocks ({region.getblockcount()} non-air)")

        # This is where the magic happens: we ask Litemapy to replace blocks according to what glassiy returns
        region.filter(glassify)

    # Display the statistics
    end = time()
    print(f"Done, processed {total_blocks} blocks in {round(end - start)}s...")

    # Save the new schematic
    print("Saving litematic...")
    litematic.save(out_file)

    print("Done.")


if __name__ == '__main__':
    # The script takes the input and output files are command line arguments
    glacify_litematic(argv[1], argv[2])
