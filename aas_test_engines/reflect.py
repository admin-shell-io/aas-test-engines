from typing import (
    List,
    Dict,
    Optional,
    Tuple,
    Union,
    ForwardRef,
    Pattern,
    Callable,
    Iterator,
)
from enum import Enum
from dataclasses import is_dataclass, fields
import re
import inspect
import base64


def abstract(cls):
    # Prefix with cls to apply only to base class
    setattr(cls, f"_{cls}_abstract", True)
    return cls


def is_abstract(cls):
    return hasattr(cls, f"_{cls}_abstract")


def _unwrap_optional(cls) -> Tuple[bool, type]:
    try:
        origin = cls.__origin__
    except AttributeError:
        return True, cls
    if origin is not Union:
        return True, cls
    # We only support Optional aka. Union[x, NoneType]
    assert len(cls.__args__) == 2 and cls.__args__[1] is type(None)
    return False, cls.__args__[0]


def _unwrap_forward_ref(cls, globals, locals) -> Tuple[type]:
    if isinstance(cls, ForwardRef):
        try:
            try:
                return cls._evaluate(globals, locals, recursive_guard=frozenset())
            except TypeError:
                # Python < 3.9
                return cls._evaluate(globals, locals)
        except NameError as e:
            raise Exception(f"{e}: Have you tried passing globals() and locals() to reflect?")
    else:
        return cls


class StringFormattedValue:
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[Pattern] = None
    base64: bool = False

    def __init__(self, raw_value: str):
        self.raw_value = raw_value
        if self.min_length is not None:
            if len(raw_value) < self.min_length:
                raise ValueError(f"String is shorter than {self.min_length} characters")
        if self.max_length is not None:
            if len(raw_value) > self.max_length:
                raise ValueError(f"String is longer than {self.max_length} characters")

        # Constraint AASd-130: An attribute with data type "string" shall be restricted to the characters as defined in
        # XML Schema 1.0, i.e. the string shall consist of these characters only: ^[\x09\x0A\x0D\x20-\uD7FF\uE000-
        # \uFFFD\u00010000-\u0010FFFF]*$.
        if (
            re.fullmatch(
                r"[\x09\x0a\x0d\x20-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]*",
                raw_value,
            )
            is None
        ):
            raise ValueError("Constraint AASd-130 violated: String is not XML serializable")

        if self.pattern:
            if re.fullmatch(self.pattern, raw_value) is None:
                raise ValueError(f"String '{raw_value}' does not match pattern {self.pattern}")

    def __eq__(self, other: "StringFormattedValue") -> bool:
        return self.raw_value == other.raw_value

    def __str__(self) -> str:
        if self.base64:
            return base64.urlsafe_b64encode(self.raw_value.encode()).decode()
        else:
            return self.raw_value


class TypeBase:
    def construct(self, args: Dict[str, any]):
        raise NotImplementedError(self)


class NoneType(TypeBase):
    pass


class StringType(TypeBase):
    pass


class BoolType(TypeBase):
    pass


class AnyType(TypeBase):
    pass


class NumberType(TypeBase):
    pass


class BytesType(TypeBase):
    pass


class EnumType(TypeBase):
    def __init__(self, cls):
        self.cls = cls

    def construct(self, args):
        return self.cls(args)


class FunctionType(AnyType):
    class Argument:
        def __init__(self, name: str, type: TypeBase, required: bool):
            self.name = name
            self.type = type
            self.required = required

        def __eq__(self, other):
            assert isinstance(other, FunctionType.Argument)
            if self.name != other.name:
                return False
            if self.required != other.required:
                return False
            # TODO: check type
            return True

    def __init__(self, func: callable, return_type: TypeBase, args: List[Argument]):
        self.func = func
        self.return_type = return_type
        self.args = args

    def __eq__(self, other) -> bool:
        assert isinstance(other, FunctionType)
        return self.args == other.args


class ClassType(TypeBase):
    class Attribute:
        def __init__(self, name: str, type: TypeBase, required: bool, force_name: Optional[str]):
            self.name = name
            self.type = type
            self.required = required
            self.force_name = force_name

    def __init__(
        self,
        cls,
        attrs: List[Attribute],
        static_attrs: Dict[str, any],
        subclasses: List["ClassType"],
    ):
        self.cls = cls
        self.attrs = attrs
        self.static_attrs = static_attrs
        self.subclasses = subclasses

    def construct(self, args):
        return self.cls(**{**args, **self.static_attrs})

    def is_abstract(self) -> bool:
        return is_abstract(self.cls)


class ListType(TypeBase):
    def __init__(self, item_type: TypeBase, allow_empty: bool):
        self.item_type = item_type
        self.allow_empty = allow_empty


class StringFormattedValueType(TypeBase):
    def __init__(self, cls):
        self.cls: StringFormattedValue = cls

    def construct(self, args):
        return self.cls(args)


class UnresolvedType(TypeBase):

    def __init__(self, cls):
        self.ref_cls = cls


def _collect_subclasses(cls):
    for i in cls.__subclasses__():
        if not is_abstract(i):
            yield i
        yield from _collect_subclasses(i)


class SymbolTable:

    MissingRef = object()

    def __init__(self):
        self.symbols: Dict[str, TypeBase] = {}

    def dump(self):
        for key, value in self.symbols.items():
            print(f"{key:80}: {value}")

    def resolve(self):
        for name, symbol in self.symbols.items():
            if isinstance(symbol, ClassType):
                for field in symbol.attrs:
                    assert isinstance(field.type, UnresolvedType)
                    field.type = self.symbols[str(field.type.ref_cls)]
                symbol.subclasses = [self.symbols[str(sc.ref_cls)] for sc in symbol.subclasses]
            elif isinstance(symbol, ListType):
                assert isinstance(symbol.item_type, UnresolvedType)
                symbol.item_type = self.symbols[str(symbol.item_type.ref_cls)]


def _reflect_list(item_cls, globals, locals, symbol_table: SymbolTable, allow_empty: bool) -> ClassType:
    item_cls = _unwrap_forward_ref(item_cls, globals, locals)
    _reflect(item_cls, globals, locals, symbol_table, False)
    return ListType(UnresolvedType(item_cls), allow_empty)


def _reflect_class(cls, globals, locals, symbol_table: SymbolTable) -> ClassType:
    assert is_dataclass(cls)
    attrs: List[ClassType.Attribute] = []
    static_attrs: Dict[str, any] = {}
    for field in fields(cls):
        required, field_type = _unwrap_optional(field.type)
        try:
            exclude_as = field.metadata["exclude_as"]
            static_attrs[field.name] = exclude_as
            continue
        except KeyError:
            pass
        force_name = field.metadata.get("force_name", None)
        allow_empty_list = field.metadata.get("allow_empty", False)
        field_type = _unwrap_forward_ref(field_type, globals, locals)
        attrs.append(ClassType.Attribute(field.name, UnresolvedType(field_type), required, force_name))
        _reflect(field_type, globals, locals, symbol_table, allow_empty_list)

    subclasses: List[TypeBase] = []
    for subclass in _collect_subclasses(cls):
        subclasses.append(UnresolvedType(subclass))
        _reflect(subclass, globals, locals, symbol_table, False)
    return ClassType(cls, attrs, static_attrs, subclasses)


def _reflect(
    cls: any, globals, locals, symbol_table: SymbolTable, allow_empty_list: bool
) -> Tuple[TypeBase, SymbolTable]:
    key = str(cls)
    try:
        return symbol_table.symbols[key]
    except KeyError:
        # Avoid infinite recursion if _reflect_unsafe calls itself again
        symbol_table.symbols[key] = None
        result = _reflect_unsafe(cls, globals, locals, symbol_table, allow_empty_list)
        symbol_table.symbols[key] = result
        return result


def _reflect_unsafe(
    cls: any, globals, locals, symbol_table: SymbolTable, allow_empty_list: bool
) -> Tuple[TypeBase, SymbolTable]:
    origin = getattr(cls, "__origin__", None)
    if origin:
        if origin is list:
            item_type = cls.__args__[0]
            return _reflect_list(item_type, globals, locals, symbol_table, allow_empty_list)
    else:
        if cls is None:
            return NoneType()
        elif cls is bool:
            return BoolType()
        elif cls is str:
            return StringType()
        elif cls is any:
            return AnyType()
        elif cls is int:
            return NumberType()
        elif cls is bytes:
            return BytesType()
        elif isinstance(cls, Enum.__class__):
            return EnumType(cls)
        elif issubclass(cls, StringFormattedValue):
            return StringFormattedValueType(cls)
        elif inspect.isclass(cls):
            if not is_dataclass(cls):
                raise Exception(f"Classes must be dataclasses, but {cls} is not. Maybe you forgot to add @dataclass?")
            return _reflect_class(cls, globals, locals, symbol_table)

    raise NotImplementedError(
        f"There is no reflection implemented for:\n"
        f"  origin:    {origin}\n"
        f"  args:      {getattr(cls, '__args__', None)}\n"
        f"  cls:       {cls}\n"
    )


def reflect(cls: any, globals={}, locals={}) -> Tuple[TypeBase, SymbolTable]:
    symbol_table = SymbolTable()
    type = _reflect(cls, globals, locals, symbol_table, False)
    symbol_table.resolve()
    return type, symbol_table


def reflect_function(fn: callable, globals={}, locals={}) -> FunctionType:
    symbol_table = SymbolTable()
    return_type = fn.__annotations__.get("return", None)
    r_return_type = _reflect(return_type, globals, locals, symbol_table, False)
    args: List[FunctionType.Argument] = []
    for key, value in fn.__annotations__.items():
        if key in ["return"]:
            continue
        required, arg_type = _unwrap_optional(value)
        r_arg_type = _reflect(arg_type, globals, locals, symbol_table, False)
        args.append(FunctionType.Argument(key, r_arg_type, required))
    return FunctionType(fn, r_return_type, args)
