from json import dumps
from nbtlib.tag import Int, Double, String, List, Compound, Base
from typing_extensions import deprecated

from .deprecation import deprecated_name
from .storage import DiscriminatingDictionary

from typing import Any, Optional, Union, Iterable

EntityPosition = tuple[float, float, float]
EntityRotation = tuple[float, float]
EntityMotion = tuple[float, float, float]

BlockPosition = tuple[int, int, int]


class BlockState:
    """
    Represents an in-game block.
    :class:`BlockState` are immutable.
    """

    __block_id: str
    __properties: DiscriminatingDictionary
    __identifier_cache: Optional[str]

    def __init__(self, block_id: str, **properties: str) -> None:
        """
        A block state has a block ID and a dictionary of properties.

        :param block_id:    the identifier of the block (e.g. *minecraft:stone*)
        :param properties:  the properties of the block state as keyword parameters (e.g. *facing="north"*)
        """
        self.__block_id = assert_valid_identifier(block_id)
        self.__properties = DiscriminatingDictionary(self.__validate, properties)
        self.__identifier_cache = None

    def to_nbt(self) -> Compound:
        """
        Writes this block state to an nbt tag.
        """
        root = Compound()
        root["Name"] = String(self.id)
        properties: dict[str, str] = {String(k): String(v) for k, v in self.__properties.items()}
        if len(properties) > 0:
            root["Properties"] = Compound(properties)
        return root

    @deprecated_name("fromnbt")
    @staticmethod
    def from_nbt(nbt: Compound) -> 'BlockState':
        """
        Reads a :class:`BlockState` from an nbt tag.
        """
        block_id = assert_valid_identifier(str(nbt["Name"]))
        if "Properties" in nbt:
            properties: dict[str, str] = {str(k): str(v) for k, v in nbt["Properties"].items()}
        else:
            properties: dict[str, str] = {}
        block = BlockState(block_id, **properties)
        return block

    @property
    def id(self) -> str:
        """
        The block's identifier.
        """
        return self.__block_id

    @property
    @deprecated("Use BlockState.id instead")
    def blockid(self) -> str:
        return self.__block_id

    @deprecated_name("with_blockid")
    def with_id(self, block_id: str) -> 'BlockState':
        """
        Returns a new :class:`BlockState` with the same properties as this one but a different block id.

        :param block_id:  the block id for the new :class:`BlockState`
        """
        assert_valid_identifier(block_id)
        return BlockState(block_id, **self.__properties)

    def with_properties(self, **properties: Optional[str]) -> 'BlockState':
        """
        Returns a new copy of this :class:`BlockState` with new values for the properties given in keyword arguments.
        Using `None` as a property value removes it.

        :param properties:  the new properties as keyword arguments

        :returns: A copy of this :class:`BlockState` with the given properties updated to new values
        """
        none_properties = list(map(lambda kv: kv[0], filter(lambda kv: kv[1] is None, properties.items())))
        other = BlockState(self.id)
        other.__properties.update(self.__properties)
        for prop_name in none_properties:
            other.__properties.pop(prop_name)
            properties.pop(prop_name)
        other.__properties.update(properties)
        return other

    def properties(self) -> Iterable[tuple[str, str]]:
        """
        Exposes the properties of this :class:`BlockState` using an iterator over its properties, in a similar fashion as :func:`dict.items()`.

        :returns: An iterable over the properties, as property, value tuples.
        """
        return self.__properties.items()

    def __validate(self, k: Any, v: Any) -> tuple[bool, str]:
        if type(k) is not str or type(v) is not str:
            return False, "BlockState properties should be a string => string dictionary"
        return True, ""

    def to_block_state_identifier(self, skip_empty: bool = True) -> str:
        """
        Returns an identifier that represents the BlockState in the Sponge Schematic Format (version 2).
        Format: block_type[properties]
        Example: minecraft:oak_sign[rotation=0,waterlogged=false]

        :param skip_empty:  Whether empty brackets should be excluded if the BlockState has no properties.

        :returns: An identifier that represents the BlockState in a Sponge schematic.
        """

        if skip_empty and self.__identifier_cache is not None:
            # The result is cached when skip_empty is True,
            # but this function is used to implement __hash__,
            # so we can use functools.cache
            return self.__identifier_cache

        # TODO Needs unit tests

        identifier: str = self.__block_id
        if not skip_empty or len(self.__properties) > 0:
            state = dumps(self.__properties, separators=(',', '='), sort_keys=True)
            state = state.replace('{', '[').replace('}', ']')
            state = state.replace('"', '').replace("'", '')
            identifier += state

        if skip_empty:
            self.__identifier_cache = identifier

        return identifier

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BlockState):
            return False
        return other.__block_id == self.__block_id and other.__properties == self.__properties

    def __hash__(self) -> int:
        return hash(self.to_block_state_identifier())

    def __repr__(self) -> str:
        return self.to_block_state_identifier(skip_empty=True)

    def __getitem__(self, key: str) -> Optional[str]:
        return self.__properties[key]

    def __len__(self) -> int:
        return len(self.__properties)

    def __contains__(self, key: str) -> bool:
        return key in self.__properties


class Entity:
    """
    A Minecraft entity.
    Each entity is identified by a type identifier (e.g. minecraft:skeleton)
    and has a position within a region, as well as a rotation and a velocity vector.
    Most also have arbitrary data depending on their type
    (e.g. a sheep has a tag for its color and one indicating whether it has been sheared).
    """

    _id: str
    _data: Compound
    _position: EntityPosition
    _rotation: EntityRotation
    _motion: EntityMotion

    # TODO Needs unit tests

    def __init__(self, str_or_nbt: Union[str, Compound]) -> None:
        # TODO Refactor to only have a from_nbt static method instead of allowing nbt into the constructor
        """
        :param str_or_nbt:  either the entity identifier as a string, in which case all other tag will be default,
                            or an bnt compound tag with the entitie's data.
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

        self._id = assert_valid_identifier(self._data['id'])
        position = [float(coord) for coord in self._data['Pos']]
        self._position = (position[0], position[1], position[2])
        rotation = [float(coord) for coord in self._data['Rotation']]
        self._rotation = (rotation[0], rotation[1])
        motion = [float(coord) for coord in self._data['Motion']]
        self._motion = (motion[0], motion[1], motion[2])

    def to_nbt(self) -> Compound:
        """
        Save this entity as an NBT tag.
        """
        return self._data

    @deprecated_name("fromnbt")
    @staticmethod
    def from_nbt(nbt: Compound) -> 'Entity':
        """
        Read an entity from an nbt tag.

        :param nbt: An NBT tag with the entity's data
        """
        return Entity(nbt)

    def add_tag(self, key: str, tag) -> None:
        self._data[key] = tag
        if key == 'id':
            self._id = str(tag)
        if key == 'Pos':
            position = [float(coord) for coord in tag]
            self._position = (position[0], position[1], position[2])
        if key == 'Rotation':
            rotation = [float(coord) for coord in tag]
            self._rotation = (rotation[0], rotation[1])
        if key == 'Motion':
            motion = [float(coord) for coord in tag]
            self._motion = (motion[0], motion[1], motion[2])

    def get_tag(self, key: str) -> Base:
        try:
            return self._data[key]
        except KeyError:
            raise

    @property
    def data(self) -> Compound:
        # TODO Not documented because it exposes NBT
        return self._data

    @data.setter
    def data(self, data: Compound) -> None:
        # TODO Not documented because it exposes NBT
        self._data = Entity(data).data
        self._id = str(self._data['id'])
        position = [float(coord) for coord in self._data['Pos']]
        self._position = (position[0], position[1], position[2])
        rotation = [float(coord) for coord in self._data['Rotation']]
        self._rotation = (rotation[0], rotation[1])
        motion = [float(coord) for coord in self._data['Motion']]
        self._motion = (motion[0], motion[1], motion[2])

    @property
    def id(self) -> str:
        """
        This entity's type identifier (e.g. *minecraft:pig* )
        """
        return self._id

    @id.setter
    def id(self, id: str) -> None:
        self._id = id
        self._data['id'] = String(self._id)

    @property
    def position(self) -> EntityPosition:
        """
        The position of the entity.
        """
        return self._position

    @position.setter
    def position(self, position: EntityPosition) -> None:
        self._position = position
        self._data['Pos'] = List[Double]([Double(coord) for coord in self._position])

    @property
    def rotation(self) -> EntityRotation:
        """
        The rotation of the entity.
        """
        return self._rotation

    @rotation.setter
    def rotation(self, rotation: EntityRotation) -> None:
        self._rotation = rotation
        self._data['Rotation'] = List[Double]([Double(coord) for coord in self._rotation])

    @property
    def motion(self) -> EntityMotion:
        """
        The velocity vector of the entity.
        """
        return self._motion

    @motion.setter
    def motion(self, motion: EntityMotion) -> None:
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
    _data: Compound
    _position: BlockPosition

    def __init__(self, nbt: Compound) -> None:
        # TODO Not documented because it only exposes NBT
        self._data = nbt
        keys = self._data.keys()

        if 'x' not in keys:
            self._data['x'] = Int(0)
        if 'y' not in keys:
            self._data['y'] = Int(0)
        if 'z' not in keys:
            self._data['z'] = Int(0)
        position = [int(self._data[coord]) for coord in ['x', 'y', 'z']]
        self._position = (position[0], position[1], position[2])

    def to_nbt(self) -> Compound:
        """
        Saves the tile entity to NBT tag.
        """
        return self._data

    @deprecated_name("fromnbt")
    @staticmethod
    def from_nbt(nbt: Compound) -> 'TileEntity':
        """
        Reads a tile entity from an NBT tag.

        :param nbt: the tile entity's data as an NBT tag
        """
        return TileEntity(nbt)

    def add_tag(self, key: str, tag) -> None:
        # TODO Not documented because it exposes NBT
        self._data[key] = tag

        pos: tuple[int, int, int] = self._position
        if key == 'x':
            self._position = (int(tag), pos[1], pos[2])
        if key == 'y':
            self._position = (pos[0], int(tag), pos[2])
        if key == 'z':
            self._position = (pos[0], pos[1], int(tag))

    def get_tag(self, key: str) -> Base:
        # TODO Not documented because it exposes NBT
        try:
            return self._data[key]
        except KeyError:
            raise

    @property
    def data(self) -> Compound:
        # TODO Not documented because it exposes NBT
        return self._data

    @data.setter
    def data(self, data: Compound):
        self._data = TileEntity(data).data
        position = [int(self._data[coord]) for coord in ['x', 'y', 'z']]
        self._position = (position[0], position[1], position[2])

    @property
    def position(self) -> BlockPosition:
        """
        The tile entity's position within the :class:`Region`/
        """
        return self._position

    @position.setter
    def position(self, position: BlockPosition):
        self._position = position
        for coord, index in [('x', 0), ('y', 1), ('z', 2)]:
            self._data[coord] = Int(self._position[index])


def is_valid_identifier(identifier: str) -> bool:
    """
    Checks if a string is a valid identifier (aka. ResourceLocation in Mojmap).
    """
    # Check taken from Minecraft 1.20.1 ResourceLocation
    allowed_chars = "_-abcdefghijklmnopqrstuvwxyz0123456789.:"
    separator = False
    for char in identifier:
        if char not in allowed_chars:
            return False
        if char == ":":
            # Now parsing the path part
            separator = True
            allowed_chars = "_-abcdefghijklmnopqrstuvwxyz0123456789./"
    return separator


class InvalidIdentifier(ValueError):
    identifier: str

    def __init__(self, identifier: str) -> None:
        super().__init__(f'Invalid identifier "{identifier}"')


def assert_valid_identifier(identifier: str) -> str:
    """
    Checks whether a string is a valid identifier (aka  ResourceLocation in Mojmap),
    and raises InvalidIdentifierError if it is not.
    The name "identifier" is from Yarn mappings but makes more sens in this context.

    :returns: the identifier
    :raises CorruptedSchematicError: if provided string is not a valid identifier
    """

    if not is_valid_identifier(identifier):
        raise InvalidIdentifier(identifier)
    return identifier


class RequiredKeyMissingException(Exception):

    def __init__(self, key: str, message: str = 'The required key is missing in the (Tile)Entity\'s NBT Compound'):
        self.key = key
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return f'{self.key} -> {self.message}'
