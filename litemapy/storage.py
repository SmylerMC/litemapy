from math import ceil
import struct


class LitematicaBitArray:

    def __init__(self, size, nbits):
        self.size = size
        self.nbits = nbits
        s = ceil(nbits * size / 8)
        self.store = b''*s

    def fromnbtlongarray(arr, size, nbits):
        #TODO Check if size is compatible with long array length
        buff = b''
        for l in arr:
            buff += struct.pack('<q', int(l)) #TODO Make sure this is right
        r = LitematicaBitArray(size, nbits)
        r.store = buff
        #print(buff)
        return r

    def __getitem__(self, index):
        startoff = index * self.nbits
        startind = startoff // 8
        endoff = (index + 1) * self.nbits
        endind = ceil(endoff / 8)
        sbitoff = startoff % 8
        ebitoff = endoff % 8
        #print(startoff, startind, endoff, endind, sbitoff, ebitoff)
        v = 0
        for i, b in enumerate(self.store[startind: endind]):
            bitadded = 8
            #print(b)
            if i == endind - startind - 1:
                b >>= (8 - ebitoff) % 8
                bitadded -= (8 - ebitoff) % 8
                #print(b, bitadded)
            if i == 0:
                b &= (1 << (8-sbitoff)) - 1
                bitadded -= sbitoff
                #print(b, bitadded)
            #print(b)
            #print()
            v <<= bitadded
            #print(bitadded)
            v += b
        return v

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

