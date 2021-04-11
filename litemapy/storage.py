from math import ceil
import nbtlib.tag

class LitematicaBitArray:

    def __init__(self, size, nbits):
        self.size = size
        self.nbits = nbits
        s = ceil(nbits * size / 64)
        self.array = [0] * s
        self.__mask = (1 << nbits) - 1 # nbits bits set to 1

    def fromnbtlongarray(arr, size, nbits):
        excpected_len = ceil(size * nbits / 64)
        if excpected_len != len(arr):
            raise ValueError(
                "long array length does not match bit array size and nbits, excpected {}, not {}".format(
                        excpected_len, len(arr)
                    )
                )
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
                i |= ~m2 # Add the potential infinit 1 prefix for negative numbers
            l.append(i)
        return l

    def _tonbtlongarray(self):
        return nbtlib.tag.LongArray(self._tolonglist())

    def __getitem__(self, index):
        if not 0 <= index < len(self):
            raise IndexError("Invalid index {}".format(index))
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
        if not 0 <= index < len(self):
            raise IndexError("Invalid index {}".format(index))
        if not 0 <= value <= self.__mask:
            raise ValueError("Invalid value {}, maximum value is {}".format(value, self.__mask))
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
        for i in range(len(self)):
            yield self[i]

    def __reversed__(self):
        arr = LitematicaBitArray(self.size, self.nbits)
        for i in range(len(self)):
            arr[i] = self[len(self) - i - 1]
        return arr
    
    def __contains__(self, value):
        for v in self:
            if v == value:
                return True
        return False

class DiscriminatingDictionnary(dict):

    def __init__(self, validator, *args, **options):
        """
        validator: a function that takes as argument a key and an item and returns a tuple (canstore, msg)
        canstore must be a boolean, True if the item is accepted, and False otherwwise
        if canstore is false, msg will be used as the error message
        onadd: an optional function that gets called when an item is added to the dictionnary, with the key and item as arguments. On add is not called for the values that might have been passed in the constructor.
        """
        #TODO Handle iterators in constructor
        self.validator = validator
        if "onadd" in options:
            self.onadd = options.pop("onadd")
        else:
            self.onadd = None
        if "onremove" in options:
            self.onremove = options.pop("onremove")
        else:
            self.onremove = None
        if len(args) == 1 and type(args[0]) == dict:
            for key, item in args[0].items():
                self.validate(key, item)
            options = args[0]
        else:
            for key, item in args:
                self.validate(key, item)
        for key, item in options.items():
            self.validate(key, item)
        super().__init__(*args, **options)

    def validate(self, key, item):
        canstore, msg = self.validator(key, item)
        if not canstore:
            raise DiscriminationError(msg)

    def __setitem__(self, key, item):
        self.validate(key, item)
        b = key in self
        old = self.get(key)
        super().__setitem__(key, item)
        if b:
            self.__onrm(key, old)
        self.__onadd(key, item)

    def __delitem__(self, key):
        if key not in self:
            raise KeyError()
        v = self[key]
        super().__delitem__(key)
        self.__onrm(key, v)

    def setdefault(self, key, *args):
        default = args[0] if len(args) > 0 else None
        self.validate(key, default)
        b =  key not in self
        r = super().setdefault(key, default)
        if b:
            self.__onadd(key, default)
        return r

    def update(self, other):
        other = DiscriminatingDictionnary(self.validator, other)
        for k, v in other.items():
            self[k] = v

    def pop(self, key):
        v = super().pop(key)
        self.__onrm(key, v)

    def popitem(self):
        k, v = super().popitem()
        self.__onrm(k, v)

    def clear(self):
        c = self.copy()
        super().clear()
        for k, v in c.items():
            self.__onrm(k, v)

    def __onadd(self, key, item):
        if self.onadd is not None:
            self.onadd(key, item)

    def __onrm(self, key, item):
        if self.onremove is not None:
            self.onremove(key, item)

class DiscriminationError(Exception):
    pass
