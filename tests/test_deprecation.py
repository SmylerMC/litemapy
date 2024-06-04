from litemapy.deprecation import deprecated_name


def test_deprecated_name():

    class A:

        def __init__(self):
            self.g = None

        @deprecated_name("c")
        def b(self, arg, kwarg="default"):
            return arg, kwarg

        @deprecated_name("e")
        @staticmethod
        def d(arg, kwarg="default"):
            return arg, kwarg

        @property
        @deprecated_name("h")
        def prop(self):
            return self.g

        @prop.setter
        def prop(self, val):
            self.g = val

    a = A()
    assert a.b("hello", kwarg="world") == ("hello", "world")
    assert a.c("hello", kwarg="world") == ("hello", "world")
    assert a.d("lorem", kwarg="ipsum") == ("lorem", "ipsum")
    assert a.e("lorem", kwarg="ipsum") == ("lorem", "ipsum")
    assert A.d("lorem", kwarg="ipsum") == ("lorem", "ipsum")
