from aas_test_engines.reflect import (
    reflect,
    reflect_function,
    ClassType,
    StringType,
    ListType,
    StringFormattedValue,
    abstract,
    FunctionType,
    NoneType,
)
from unittest import TestCase, main
from dataclasses import dataclass, field
from typing import Optional, List


class TestReflect(TestCase):

    def test_abstract(self):
        @dataclass
        @abstract
        class Foo:
            pass

        type, table = reflect(Foo)
        assert isinstance(type, ClassType)
        self.assertTrue(type.is_abstract())

    def test_simple_class(self):

        @dataclass
        class Foo:
            bar: str

        type, table = reflect(Foo)
        assert isinstance(type, ClassType)
        self.assertIsInstance(type.attrs[0].type, StringType)
        self.assertEqual(type.attrs[0].name, "bar")
        self.assertEqual(len(table.symbols), 2)
        type.construct({"bar": "foo"})

    def test_nested_class(self):

        @dataclass
        class Bar:
            pass

        @dataclass
        class Foo:
            bar: Bar

        type, table = reflect(Foo)
        assert isinstance(type, ClassType)
        assert isinstance(type.attrs[0].type, ClassType)
        self.assertEqual(len(type.attrs), 1)
        self.assertEqual(len(table.symbols), 2)

    def test_forward_ref(self):
        @dataclass
        class Bar:
            foo: Optional["Foo"]

        @dataclass
        class Foo:
            pass

        type, table = reflect(Bar, globals(), locals())
        assert isinstance(type, ClassType)
        assert isinstance(type.attrs[0].type, ClassType)
        self.assertEqual(len(type.attrs), 1)
        self.assertEqual(len(table.symbols), 2)

    def test_list(self):
        @dataclass
        class Foo:
            pass

        @dataclass
        class Bar:
            foo: List[Foo]

        type, table = reflect(Bar, globals(), locals())
        assert isinstance(type, ClassType)
        foo = type.attrs[0]
        self.assertEqual(foo.name, "foo")
        assert isinstance(foo.type, ListType)
        assert isinstance(foo.type.item_type, ClassType)
        self.assertEqual(len(table.symbols), 3)

    def test_recursion(self):
        @dataclass
        class Bar:
            foo: Optional["Foo"]

        @dataclass
        class Foo:
            bar: List[Bar]

        type, table = reflect(Bar, globals(), locals())
        assert isinstance(type, ClassType)
        assert isinstance(type.attrs[0].type, ClassType)
        self.assertEqual(type.attrs[0].name, "foo")
        self.assertFalse(type.attrs[0].required)
        self.assertEqual(len(type.attrs), 1)
        self.assertEqual(len(table.symbols), 3)

    def test_optional(self):
        @dataclass
        class Bar:
            foo: Optional[str]
            bar: str

        type, table = reflect(Bar, globals(), locals())
        assert isinstance(type, ClassType)
        foo = type.attrs[0]
        self.assertEqual(foo.name, "foo")
        bar = type.attrs[1]
        self.assertEqual(bar.name, "bar")
        assert isinstance(foo.type, StringType)
        self.assertFalse(foo.required)
        assert isinstance(bar.type, StringType)
        self.assertTrue(bar.required)
        self.assertEqual(len(type.attrs), 2)
        self.assertEqual(len(table.symbols), 2)

    def test_string_formatted_value(self):
        @dataclass
        class Foo:
            bar: StringFormattedValue

        type, table = reflect(Foo)
        assert isinstance(type, ClassType)
        self.assertEqual(len(table.symbols), 2)

    def test_exclude_as(self):
        @dataclass
        class Foo:
            bar: str = field(metadata={"exclude_as": 42})

        type, table = reflect(Foo)
        assert isinstance(type, ClassType)
        self.assertEqual(len(type.attrs), 0)
        self.assertEqual(len(table.symbols), 1)
        type.construct({})

    def test_subclasses(self):
        @dataclass
        class Foo:
            pass

        @dataclass
        class Bar(Foo):
            pass

        @dataclass
        class Baz(Bar):
            pass

        type, table = reflect(Foo)
        self.assertEqual(len(table.symbols), 3)
        assert isinstance(type, ClassType)
        self.assertEqual(len(type.subclasses), 2)
        self.assertIs(type.subclasses[0].cls, Bar)
        self.assertIs(type.subclasses[1].cls, Baz)


class TestReflectFunction(TestCase):

    def test_simple(self):
        def fn():
            pass

        result = reflect_function(fn)
        assert isinstance(result, FunctionType)
        assert isinstance(result.return_type, NoneType)
        self.assertEqual(len(result.args), 0)

    def test_return(self):
        def fn() -> str:
            pass

        result = reflect_function(fn)
        assert isinstance(result, FunctionType)
        assert isinstance(result.return_type, StringType)
        self.assertEqual(len(result.args), 0)

    def test_args(self):
        def fn(foo: str):
            pass

        result = reflect_function(fn)
        assert isinstance(result, FunctionType)
        self.assertEqual(len(result.args), 1)
        self.assertEqual(result.args[0].name, "foo")
        assert isinstance(result.args[0].type, StringType)
        self.assertTrue(result.args[0].required)

    def test_optional(self):
        def fn(foo: Optional[str]):
            pass

        result = reflect_function(fn)
        assert isinstance(result, FunctionType)
        self.assertEqual(len(result.args), 1)
        self.assertEqual(result.args[0].name, "foo")
        assert isinstance(result.args[0].type, StringType)
        self.assertFalse(result.args[0].required)

    def test_complex(self):
        @dataclass
        class Foo:
            abc: List[str]

        def fn(foo: Foo, bar: str) -> Foo:
            pass

        result = reflect_function(fn)
        assert isinstance(result, FunctionType)
        self.assertEqual(len(result.args), 2)
        self.assertEqual(result.args[0].name, "foo")
        assert isinstance(result.args[0].type, ClassType)
        self.assertEqual(result.args[1].name, "bar")
        assert isinstance(result.args[1].type, StringType)
        assert isinstance(result.return_type, ClassType)

    def test_equal(self):
        def fn1(foo: str) -> str:
            pass

        def fn2(foo: str):
            pass

        def fn3(foo: str, bar: str):
            pass

        t1 = reflect_function(fn1)
        t2 = reflect_function(fn2)
        t3 = reflect_function(fn3)
        self.assertEqual(t1, t2)
        self.assertNotEqual(t1, t3)
        self.assertNotEqual(t2, t3)


if __name__ == "__main__":
    main()
