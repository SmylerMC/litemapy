from math import ceil
import nbtlib.tag


class LitematicaBitArray:

    def __init__(self, size, nbits):
        self.size = size
        self.nbits = nbits
        s = ceil(nbits * size / 64)
        self.array = [0] * s
        self.__mask = (1 << nbits) - 1  # nbits bits set to 1

    @staticmethod
    def fromnbtlongarray(arr, size, nbits):
        # TODO Test loading and validating from an external source
        expected_len = ceil(size * nbits / 64)
        if expected_len != len(arr):
            raise ValueError(
                "long array length does not match bit array size and nbits, expected {}, not {}".format(
                        expected_len, len(arr)
                    )
                )
        r = LitematicaBitArray(size, nbits)
        m = (1 << 64) - 1
        r.array = [int(i) & m for i in arr]  # Remove the infinite trailing 1s of negative numbers
        return r

    def _tolonglist(self):
        list_of_longs = []
        m1 = 1 << 63
        m2 = (1 << 64) - 1
        for i in self.array:
            if i & m1 > 0:
                i |= ~m2  # Add the potential infinite 1 prefix for negative numbers
            list_of_longs.append(i)
        return list_of_longs

    def _tonbtlongarray(self):
        return nbtlib.tag.LongArray(self._tolonglist())

    def __getitem__(self, index):
        if not 0 <= index < len(self):
            raise IndexError("Invalid index {}".format(index))
        start_offset = index * self.nbits
        start_arr_index = start_offset >> 6
        end_arr_index = ((index + 1) * self.nbits - 1) >> 6
        start_bit_offset = start_offset & 0x3F

        if start_arr_index == end_arr_index:
            return self.array[start_arr_index] >> start_bit_offset & self.__mask
        else:
            end_offset = 64 - start_bit_offset
            val = self.array[start_arr_index] >> start_bit_offset | self.array[end_arr_index] << end_offset
            return val & self.__mask

    def __setitem__(self, index, value):
        if not 0 <= index < len(self):
            raise IndexError("Invalid index {}".format(index))
        if not 0 <= value <= self.__mask:
            raise ValueError("Invalid value {}, maximum value is {}".format(value, self.__mask))
        start_offset = index * self.nbits
        start_arr_index = start_offset >> 6
        end_arr_index = ((index + 1) * self.nbits - 1) >> 6
        start_bit_offset = start_offset & 0x3F
        m = (1 << 64) - 1
        zeroed = self.array[start_arr_index] & ~(self.__mask << start_bit_offset)
        updated = zeroed | (value & self.__mask) << start_bit_offset
        self.array[start_arr_index] = updated & m

        if start_arr_index != end_arr_index:
            end_offset = 64 - start_bit_offset
            j1 = self.nbits - end_offset
            self.array[end_arr_index] = (self.array[end_arr_index] >> j1 << j1 | (value & self.__mask) >> end_offset) & m

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


class DiscriminatingDictionary(dict):

    def __init__(self, validator, *args, **options):
        """
        :params validator:  a function that takes as argument a key and an item and returns a tuple (canstore, msg)
                            canstore must be a boolean, True if the item is accepted, and False otherwise
                            if canstore is false, msg will be used as the error message
        :param onadd:       an optional function that gets called when an item is added to the dictionary,
                            with the key and item as arguments.
                            onadd is not called for the values that might have been passed in the constructor.
        """
        # TODO Handle iterators in constructor
        self.validator = validator
        self.onadd = options.pop("onadd", None)
        self.onremove = options.pop("onremove", None)
        if len(args) == 1 and isinstance(args[0], dict):
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
        b = key not in self
        r = super().setdefault(key, default)
        if b:
            self.__onadd(key, default)
        return r

    def update(self, other):
        other = DiscriminatingDictionary(self.validator, other)
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
