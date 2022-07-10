class CorruptedSchematicError(Exception):
    pass


class RequiredKeyMissingException(Exception):

    def __init__(self, key, message='The required key is missing in the (Tile)Entity\'s NBT Compound'):
        self.key = key
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.key} -> {self.message}'
