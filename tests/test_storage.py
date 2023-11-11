import pytest
import litemapy.storage as storage
import math

TEST_VALUES = 0, 0, 0, 12, 13, 0, 4, 0, 2, 4, 1, 3, 3, 7, 65, 9


def test_write_read_to_litematica_bit_array():
    nbits = math.ceil(math.log(max(TEST_VALUES), 2)) + 1
    arr = storage.LitematicaBitArray(len(TEST_VALUES), nbits)
    for i, e in enumerate(TEST_VALUES):
        arr[i] = e
    for i, e in enumerate(TEST_VALUES):
        print(i, e)
        assert e == arr[i]


def test_invalid_access_to_litematica_bit_array_raises_exceptions():
    arr = storage.LitematicaBitArray(10, 4)
    with pytest.raises(IndexError):
        arr[-1] = 0
    with pytest.raises(IndexError):
        arr[10] = 0
    with pytest.raises(ValueError):
        arr[0] = -1
    with pytest.raises(ValueError):
        arr[0] = 16


def test_litematica_bit_array_in():
    nbits = math.ceil(math.log(max(TEST_VALUES), 2)) + 1
    array = storage.LitematicaBitArray(len(TEST_VALUES), nbits)
    for i, e in enumerate(TEST_VALUES):
        array[i] = e
    assert 13 in array
    assert 15 not in array


def test_basic_set_get():
    def discriminator(k, v):
        print("Discriminating ", type(k), k, "=>", type(v), v)
        return v >= 0, "Need pos"

    discriminating_dictionary = storage.DiscriminatingDictionary(discriminator)
    discriminating_dictionary["0"] = 0
    assert discriminating_dictionary["0"] == 0
    assert "0" in discriminating_dictionary
    assert "0" in discriminating_dictionary.keys()
    assert 0 in discriminating_dictionary.values()
    assert discriminating_dictionary.get("1") is None
    with pytest.raises(storage.DiscriminationError):
        discriminating_dictionary['-1'] = -1
    other_dictionary = {"1": 1, "2": 2}
    discriminating_dictionary.update(other_dictionary)
    assert "1" in discriminating_dictionary
    assert "2" in discriminating_dictionary
    with pytest.raises(storage.DiscriminationError):
        discriminating_dictionary.update({"-1": -1})
    other_dictionary = {"1": 1, "2": 2}
    discriminating_dictionary = storage.DiscriminatingDictionary(lambda k, v: (v >= 0, "Need pos"), other_dictionary)
    assert "1" in discriminating_dictionary
    assert "2" in discriminating_dictionary
    discriminating_dictionary = storage.DiscriminatingDictionary(lambda k, v: (v >= 0, "Need pos"), a=1, b=2)
    assert "a" in discriminating_dictionary
    assert "b" in discriminating_dictionary


def test_discriminating_dictionary_onadd():
    class Counter:

        def __init__(self):
            self.counter = 0

        def on_add(self, k, v):
            self.counter += v

    c = Counter()
    dictionary = storage.DiscriminatingDictionary(
        lambda k, v: (v >= 0, "Need pos"),
        onadd=c.on_add,
        x=10
    )
    dictionary["a"] = 1
    assert c.counter == 1
    dictionary.update({"b": 2, "c": 3})
    assert c.counter == 6
    dictionary.setdefault("d", 4)
    assert c.counter == 10


def test_discriminating_dictionary_onremove():
    class Counter:
        def __init__(self):
            self.counter = 0

        def on_remove(self, k, v):
            self.counter += v

    c = Counter()
    dictionary = storage.DiscriminatingDictionary(
        lambda k, v: (v >= 0, "Need pos"),
        onremove=c.on_remove,
        a=1, b=2, c=3, d=4, x=10
    )
    del dictionary["a"]
    assert c.counter == 1
    dictionary.pop("b")
    assert c.counter == 3
    dictionary.pop("c")
    assert c.counter == 6
    dictionary.pop("d")
    assert c.counter == 10
    dictionary.popitem()
    assert c.counter == 20
    c = Counter()
    dictionary = storage.DiscriminatingDictionary(
        lambda k, v: (v >= 0, "Need pos"),
        onremove=c.on_remove,
        a=1, b=2, c=3, d=4, x=10
    )
    dictionary.clear()
    assert c.counter == 20


def test_discriminating_dictionary_onadd_onremove():
    class Counter:
        def __init__(self):
            self.added = 0
            self.removed = 0

        def on_remove(self, k, v):
            self.removed += v

        def on_add(self, k, v):
            self.added += v

    c = Counter()
    dictionary = storage.DiscriminatingDictionary(
        lambda k, v: (v >= 0, "Need pos"),
        onadd=c.on_add,
        onremove=c.on_remove,
        a=1, b=2, c=3, d=4, x=10
    )
    dictionary["c"] = 7
    assert c.added == 7
    assert c.removed == 3
    dictionary.update({"x": 100, "d": 500, "y": 200})
    assert c.added == 807
    assert c.removed == 17
