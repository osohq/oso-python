from typing import Optional, Tuple, Any
from oso_cloud import Fact, Value as OsoValue


def _process_class(cls, name=None, id=None):
    type = cls.__name__ if name is None else name
    setattr(cls, "__oso_type__", type)

    id_attr = "id" if id is None else id

    def _get_id(self) -> str:
        # TODO can fail
        return str(self.__dict__[id_attr])

    setattr(cls, "__oso_id__", _get_id)

    def _oso_type(self) -> OsoValue:
        # id: str = self.__oso_id__()
        return OsoValue(type=self.__oso_type__, id=self.__oso_id__())

    setattr(cls, "__oso_value__", _oso_type)

    return cls


def oso_type(
    cls=None,
    name: Optional[str] = None,
    id: Optional[str] = None,
):
    def wrap(cls):
        return _process_class(cls, name, id)

    # See if we're being called as @oso_type or @oso_type().
    if cls is None:
        # We're called with parens.
        return wrap

    # We're called as @oso_type without parens.
    return wrap(cls)


def to_value(instance: Any) -> OsoValue:
    if (
        isinstance(instance, int)
        or isinstance(instance, bool)
        or isinstance(instance, str)
    ):
        return _handle_primitives(instance)

    try:
        return instance.__oso_value__()
    # TODO raise informative errors here
    except Exception as e:
        raise e


def _handle_primitives(instance: int | bool | str) -> OsoValue:
    if isinstance(instance, int):
        return OsoValue(type="Integer", id=str(instance))
    if isinstance(instance, bool):
        return OsoValue(type="Boolean", id=str(instance).lower())
    if isinstance(instance, str):
        # TODO not sure if this needs to happen here
        # if instance == "":
        #     raise TypeError(
        #         "Oso: Instance cannot be an empty string. "
        #         + "For wildcards, use the empty dict ({}) or None."
        #     )
        return OsoValue(type="String", id=instance)


def to_fact(predicate: str, args: Tuple[Any, ...]) -> Fact:
    return Fact(name=predicate, args=[to_value(arg) for arg in args])
