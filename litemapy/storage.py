from math import ceil
import struct


class LitematicaBitArray:

    def __init__(self, size, nbits):
        self.size = size
        self.nbits = nbits
        s = ceil(nbits * size / 64)
        self.array = [0] * s
        self.__mask = (1 << nbits) - 1 # nbits bits set to 1

    def fromnbtlongarray(arr, size, nbits):
        #TODO Check if size is compatible with long array length
        r = LitematicaBitArray(size, nbits)
        m = (1 << 64) - 1
        r.array = [int(i) & m for i in arr] # Remove the infinite trailing 1s of negative numbers
        return r

    def _tolonglist(self):
        l = []
        m1 = 1 << 63
        m2 = (1 << 64) - 1
        for i in self.array:
            if i & m1 > 0:
                i |= ~m2
            l.append(i)
        return l


    def __getitem__(self, index):
        #TODO Check index
        startOffset = index * self.nbits
        startArrIndex = startOffset >> 6
        endArrIndex = ((index + 1) * self.nbits - 1) >> 6
        startBitOffset = startOffset & 0x3F

        if startArrIndex == endArrIndex : 
            return self.array[startArrIndex] >> startBitOffset & self.__mask
        else:
            endOffset = 64 - startBitOffset;
            return (self.array[startArrIndex] >> startBitOffset | self.array[endArrIndex] << endOffset) & self.__mask

    def __setitem__(self, index, value):
        #TODO Check index and value
        startOffset = index * self.nbits
        startArrIndex = startOffset >> 6
        endArrIndex = ((index + 1) * self.nbits - 1) >> 6
        startBitOffset = startOffset & 0x3F
        m = (1 << 64) - 1
        self.array[startArrIndex] = (self.array[startArrIndex] & ~(self.__mask << startBitOffset) | (value & self.__mask) << startBitOffset) & m

        if startArrIndex != endArrIndex:
            endOffset = 64 - startBitOffset;
            j1 = self.nbits - endOffset;
            self.array[endArrIndex] = (self.array[endArrIndex] >> j1 << j1 | ( value & self.__mask) >> endOffset) & m

    def __len__(self):
        return self.size

    def __iter__(self):
        pass #TODO

    def __reversed__(self):
        pass #TODO
    
    def __contains__(self, item):
        pass #TODO

    def _tonbtlongarray(self):
        pass #TODO

