from typing import Callable


def deprecated_name(old_name: str):
    class Wrapper:
        original: Callable

        def __init__(self, original: Callable):
            self.original = original

        def __set_name__(self, owner, name):
            setattr(owner, name, self.original)
            setattr(owner, old_name, self.original)

    return Wrapper
