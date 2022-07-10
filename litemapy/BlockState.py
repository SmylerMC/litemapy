from json import dumps
from math import ceil, log
from time import time

import nbtlib
import numpy as np
from nbtlib.tag import Short, Byte, Int, Long, Double, String, List, Compound, ByteArray, IntArray

from .info import *
from .Storage import LitematicaBitArray, DiscriminatingDictionary
from .Exception import CorruptedSchematicError, RequiredKeyMissingException





class BlockState:

    def __init__(self, blockid, properties=None):
        if properties is None:
            properties = {}
        self.__blockid = blockid
        self.__properties = DiscriminatingDictionary(self.__validate, properties)

    def _tonbt(self):
        root = Compound()
        root["Name"] = String(self.blockid)
        properties = {String(k): String(v) for k, v in self.__properties.items()}
        if len(properties) > 0:
            root["Properties"] = Compound(properties)
        return root

    @staticmethod
    def fromnbt(nbt):
        bid = str(nbt["Name"])
        if "Properties" in nbt:
            properties = {str(k): str(v) for k, v in nbt["Properties"].items()}
        else:
            properties = {}
        block = BlockState(bid, properties=properties)
        return block

    @property
    def blockid(self):
        return self.__blockid

    def __validate(self, k, v):
        if type(k) is not str or type(v) is not str:
            return False, "Blockstate properties should be a string => string dictionary"
        return True, ""

    def to_block_state_identifier(self, skip_empty=True):
        """
        Returns an identifier that represents the BlockState in the Sponge Schematic Format (version 2).
        Format: block_type[properties]
        Example: minecraft:oak_sign[rotation=0,waterlogged=false]

        Parameters
        ----------
        skip_empty : bool, default=True
            Whether empty brackets should be excluded if the BlockState has no properties.

        Returns
        -------
        identifier : str
            An identifier that represents the BlockState in a Sponge schematic.
        """

        # TODO Needs unit tests

        identifier = self.__blockid
        if skip_empty and not len(self.__properties):
            return identifier

        state = dumps(self.__properties, separators=(',', '='), sort_keys=True)
        state = state.replace('{', '[').replace('}', ']')
        state = state.replace('"', '').replace("'", '')

        identifier += state
        return identifier

    def __eq__(self, other):
        if not isinstance(other, BlockState):
            raise ValueError("Can only compare blockstates with blockstates")
        return other.__blockid == self.__blockid and other.__properties == self.__properties

    def __repr__(self):
        return self.to_block_state_identifier(skip_empty=True)

    def __getitem__(self, key):
        return self.__properties[key]

    def __len__(self):
        return len(self.__properties)
