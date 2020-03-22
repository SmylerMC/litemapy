from math import ceil
import struct


class LitematicaBitArray:

    def __init__(self, size, nbits):
        self.size = size
        self.nbits = nbits
        s = ceil(nbits * size / 8)
        self.store = b''*s

    def fromnbtlongarray(arr, si
        #TODO Check if size is compatible with long array length
        buff = b''
        for l in arr:
            buff += struct.pack('<Q', int(l)) #TODO Make sure this is right
        r = LitematicaBitArray(size, nbits)
        r.store = buff
        return r

    def __getitem__(self, key):
        pass #TODO

    def __setitem__(self, key, value):
        pass #TODO

    def __iter__(self):
        pass #TODO

    def __reversed__(self):
        pass #TODO
    
    def __contains__(self, item):
        pass #TODO

    def _tonbtlongarray(self):
        pass #TODO

