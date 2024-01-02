from json import dumps
from nbtlib.tag import Int, Double, String, List, Compound

from .storage import DiscriminatingDictionary


class BlockState:
    """
    Represents an in-game block.
    :class:`BlockState` are immutable.
    """

    def __init__(self, block_id, **properties):
        """
        A block state has a block ID and a dictionary of properties.

        :param block_id:    the identifier of the block (e.g. *minecraft:stone*)
        :type block_id:     str
        :param properties:  the properties of the block state as keyword parameters (e.g. *facing="north"*)
        :type properties:   str
        """
        self.__block_id = block_id
        self.__properties = DiscriminatingDictionary(self.__validate, properties)
        self.__identifier_cache = None

    def to_nbt(self):
        """
        Writes this block state to an nbt tag.

        :rtype: ~nbtlib.tag.Compound
        """
        root = Compound()
        root["Name"] = String(self.blockid)
        properties = {String(k): String(v) for k, v in self.__properties.items()}
        if len(properties) > 0:
            root["Properties"] = Compound(properties)
        return root

    @staticmethod
    def fromnbt(nbt):
        """
        Reads a :class:`BlockState` from an nbt tag.

        :rtype: BlockState
        """
        block_id = str(nbt["Name"])
        if "Properties" in nbt:
            properties = {str(k): str(v) for k, v in nbt["Properties"].items()}
        else:
            properties = {}
        block = BlockState(block_id, **properties)
        return block

    @property
    def blockid(self):
        """
        The block's identifier.

        :type: str
        """
        return self.__block_id

    def with_blockid(self, block_id):
        """
        Returns a new :class:`BlockState` with the same properties as this one but a different block id.

        :param block_id:  the block id for the new :class:`BlockState`
        :type  block_id:  str
        """
        return BlockState(block_id, **self.__properties)

    def with_properties(self, **properties):
        """
        Returns a new copy of this :class:`BlockState` with new values for the properties given in keyword arguments.
        Using `None` as a property value removes it.

        :param properties:  the new properties as keyword arguments
        :type properties:   str | None

        :returns: A copy of this :class:`BlockState` with the given properties updated to new values
        :rtype: BlockState
        """
        none_properties = list(map(lambda kv: kv[0], filter(lambda kv: kv[1] is None, properties.items())))
        other = BlockState(self.blockid)
        other.__properties.update(self.__properties)
        for prop_name in none_properties:
            other.__properties.pop(prop_name)
            properties.pop(prop_name)
        other.__properties.update(properties)
        return other

    def __validate(self, k, v):
        if type(k) is not str or type(v) is not str:
            return False, "BlockState properties should be a string => string dictionary"
        return True, ""

    def to_block_state_identifier(self, skip_empty=True):
        """
        Returns an identifier that represents the BlockState in the Sponge Schematic Format (version 2).
        Format: block_type[properties]
        Example: minecraft:oak_sign[rotation=0,waterlogged=false]

        :param skip_empty:  Whether empty brackets should be excluded if the BlockState has no properties.
        :type skip_empty:   bool

        :returns: An identifier that represents the BlockState in a Sponge schematic.
        :rtype: str
        """

        if skip_empty and self.__identifier_cache is not None:
            # The result is cached when skip_empty is True,
            # but this function is used to implement __hash__,
            # so we can use functools.cache
            return self.__identifier_cache

        # TODO Needs unit tests

        identifier = self.__block_id
        if not skip_empty or len(self.__properties) > 0:
            state = dumps(self.__properties, separators=(',', '='), sort_keys=True)
            state = state.replace('{', '[').replace('}', ']')
            state = state.replace('"', '').replace("'", '')
            identifier += state

        if skip_empty:
            self.__identifier_cache = identifier

        return identifier

    def __eq__(self, other):
        if not isinstance(other, BlockState):
            raise ValueError("Can only compare BlockStates with BlockStates")
        return other.__block_id == self.__block_id and other.__properties == self.__properties

    def __hash__(self):
        return hash(self.to_block_state_identifier())

    def __repr__(self):
        return self.to_block_state_identifier(skip_empty=True)

    def __getitem__(self, key):
        return self.__properties[key]

    def __len__(self):
        return len(self.__properties)


class Entity:
    """
    A Minecraft entity.
    Each entity is identified by a type identifier (e.g. minecraft:skeleton)
    and has a position within a region, as well as a rotation and a velocity vector.
    Most also have arbitrary data depending on their type
    (e.g. a sheep has a tag for its color and one indicating whether it has been sheared).
    """

    # TODO Needs unit tests

    def __init__(self, str_or_nbt):
        # TODO Refactor to only have a from_nbt static method instead of allowing nbt into the constructor
        """
        :param str_or_nbt:  either the entity identifier as a string, in which case all other tag will be default,
                            or an bnt compound tag with the entitie's data.
        :type str_or_nbt:   str | ~nbtlib.tag.Compound
        """

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

    def to_nbt(self):
        """
        Save this entity as an NBT tag.

        :rtype: ~nbtlib.tag.Compound
        """
        return self._data

    @staticmethod
    def fromnbt(nbt):
        """
        Read an entity from an nbt tag.

        :param nbt: An NBT tag with the entity's data
        :type nbt:  ~nbtlib.tag.Compound

        :rtype:     Entity
        """
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
        # TODO Not documented because it exposes NBT
        return self._data

    @data.setter
    def data(self, data):
        # TODO Not documented because it exposes NBT
        self._data = Entity(data).data
        self._id = str(self._data['id'])
        self._position = tuple([float(coord) for coord in self._data['Pos']])
        self._rotation = tuple([float(coord) for coord in self._data['Rotation']])
        self._motion = tuple([float(coord) for coord in self._data['Motion']])

    @property
    def id(self):
        """
        This entity's type identifier (e.g. *minecraft:pig* )

        :type: str
        """
        return self._id

    @id.setter
    def id(self, id):
        self._id = id
        self._data['id'] = String(self._id)

    @property
    def position(self):
        """
        The position of the entity.

        :type: tuple[float, float, float]
        """
        return self._position

    @position.setter
    def position(self, position):
        self._position = position
        self._data['Pos'] = List[Double]([Double(coord) for coord in self._position])

    @property
    def rotation(self):
        """
        The rotation of the entity.

        :type: tuple[float, float, float]
        """
        return self._rotation

    @rotation.setter
    def rotation(self, rotation):
        self._rotation = rotation
        self._data['Rotation'] = List[Double]([Double(coord) for coord in self._rotation])

    @property
    def motion(self):
        """
        The velocity vector of the entity.

        :type: tuple[float, float, float]
        """
        return self._motion

    @motion.setter
    def motion(self, motion):
        self._motion = motion
        self._data['Motion'] = List[Double]([Double(coord) for coord in self._motion])


class TileEntity:
    # TODO Needs unit tests
    """
    A tile entity, also often referred to as block entities,
    is a type of entity which complements a block state to store additional data
    (e.g. containers like chest both have a block state that stores properties
    like their id ( *minecraft:chest* ) and orientation, and tile entity that stores their content.
    For this reason, the :class:`TileEntity` class does not store an ID  but only a position.
    The ID can be inferred by looking up the :class:`BlockState` as the same position in the :class:`Region`.
    """

    def __init__(self, nbt):
        # TODO Not documented because it only exposes NBT
        self._data = nbt
        keys = self._data.keys()

        if 'x' not in keys:
            self._data['x'] = Int(0)
        if 'y' not in keys:
            self._data['y'] = Int(0)
        if 'z' not in keys:
            self._data['z'] = Int(0)

        self._position = tuple([int(self._data[coord]) for coord in ['x', 'y', 'z']])

    def to_nbt(self):
        """
        Saves the tile entity to NBT tag.

        :rtype: ~nbtlib.tag.Compound
        """
        return self._data

    @staticmethod
    def fromnbt(nbt):
        """
        Reads a tile entity from an NBT tag.

        :param nbt: the tile entity's data as an NBT tag
        :type nbt:  ~nbtlib.tag.Compound
        :rtype:     TileEntity
        """
        return TileEntity(nbt)

    def add_tag(self, key, tag):
        # TODO Not documented because it exposes NBT
        self._data[key] = tag

        pos = self._position
        if key == 'x':
            self._position = (int(tag), pos[1], pos[2])
        if key == 'y':
            self._position = (pos[0], int(tag), pos[2])
        if key == 'z':
            self._position = (pos[0], pos[1], int(tag))

    def get_tag(self, key):
        # TODO Not documented because it exposes NBT
        try:
            return self._data[key]
        except KeyError:
            raise

    @property
    def data(self):
        # TODO Not documented because it exposes NBT
        return self._data

    @data.setter
    def data(self, data):
        self._data = TileEntity(data).data
        self._position = tuple([int(self._data[coord]) for coord in ['x', 'y', 'z']])

    @property
    def position(self):
        """
        The tile entity's position within the :class:`Region`/

        :type: tuple[int, int, int]
        """
        return self._position

    @position.setter
    def position(self, position):
        self._position = position
        for coord, index in [('x', 0), ('y', 1), ('z', 2)]:
            self._data[coord] = Int(self._position[index])


class RequiredKeyMissingException(Exception):

    def __init__(self, key, message='The required key is missing in the (Tile)Entity\'s NBT Compound'):
        self.key = key
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.key} -> {self.message}'
