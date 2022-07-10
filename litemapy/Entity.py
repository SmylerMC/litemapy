from json import dumps
from math import ceil, log
from time import time

import nbtlib
import numpy as np
from nbtlib.tag import Short, Byte, Int, Long, Double, String, List, Compound, ByteArray, IntArray

from .info import *

from .Exception import CorruptedSchematicError, RequiredKeyMissingException



class Entity:

    # TODO Needs unit tests

    def __init__(self, str_or_nbt):

        if isinstance(str_or_nbt, str):
            self._data = Compound({'id': String(str_or_nbt)})
        else:
            self._data = str_or_nbt

        keys = self._data.keys()
        if 'id' not in keys:
            raise RequiredKeyMissingException('id')
        if 'Pos' not in keys:
            self._data['Pos'] = List[Double]([Double(0.), Double(0.), Double(0.)])
        if 'Rotation' not in keys:
            self._data['Rotation'] = List[Double]([Double(0.), Double(0.)])
        if 'Motion' not in keys:
            self._data['Motion'] = List[Double]([Double(0.), Double(0.), Double(0.)])

        self._id = self._data['id']
        self._position = tuple([float(coord) for coord in self._data['Pos']])
        self._rotation = tuple([float(coord) for coord in self._data['Rotation']])
        self._motion = tuple([float(coord) for coord in self._data['Motion']])

    def _tonbt(self):
        return self._data

    @staticmethod
    def fromnbt(nbt):
        return Entity(nbt)

    def add_tag(self, key, tag):
        self._data[key] = tag
        if key == 'id':
            self._id = str(tag)
        if key == 'Pos':
            self._position = (float(coord) for coord in tag)
        if key == 'Rotation':
            self._rotation = (float(coord) for coord in tag)
        if key == 'Motion':
            self._motion = (float(coord) for coord in tag)

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
        self._data = Entity(data).data
        self._id = str(self._data['id'])
        self._position = tuple([float(coord) for coord in self._data['Pos']])
        self._rotation = tuple([float(coord) for coord in self._data['Rotation']])
        self._motion = tuple([float(coord) for coord in self._data['Motion']])

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        self._id = id
        self._data['id'] = String(self._id)

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, position):
        self._position = position
        self._data['Pos'] = List[Double]([Double(coord) for coord in self._position])

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, rotation):
        self._rotation = rotation
        self._data['Rotation'] = List[Double]([Double(coord) for coord in self._rotation])

    @property
    def motion(self):
        return self._motion

    @motion.setter
    def motion(self, motion):
        self._motion = motion
        self._data['Motion'] = List[Double]([Double(coord) for coord in self._motion])
