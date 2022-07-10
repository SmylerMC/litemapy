from json import dumps
from math import ceil, log
from time import time

import nbtlib
import numpy as np
from nbtlib.tag import Short, Byte, Int, Long, Double, String, List, Compound, ByteArray, IntArray

from .info import *






class TileEntity:

    # TODO Needs unit tests

    def __init__(self, nbt):

        self._data = nbt
        keys = self._data.keys()

        if 'x' not in keys:
            self._data['x'] = Int(0)
        if 'y' not in keys:
            self._data['y'] = Int(0)
        if 'z' not in keys:
            self._data['z'] = Int(0)

        self._position = tuple([int(self._data[coord]) for coord in ['x', 'y', 'z']])

    def _tonbt(self):
        return self._data

    @staticmethod
    def fromnbt(nbt):
        return TileEntity(nbt)

    def add_tag(self, key, tag):
        self._data[key] = tag

        pos = self._position
        if key == 'x':
            self._position = (int(tag), pos[1], pos[2])
        if key == 'y':
            self._position = (pos[0], int(tag), pos[2])
        if key == 'z':
            self._position = (pos[0], pos[1], int(tag))

    def get_tag(self, key):
        try:
            return self._data[key]
        except KeyError:
            raise

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = TileEntity(data).data
        self._position = tuple([int(self._data[coord]) for coord in ['x', 'y', 'z']])

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, position):
        self._position = position
        for coord, index in [('x', 0), ('y', 1), ('z', 2)]:
            self._data[coord] = Int(self._position[index])
