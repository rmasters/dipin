from typing import Type


def is_class_type(t: Type) -> bool:
    """This is hacky, but I don't know of a good method for checking if a type is a user-defined class."""

    return t not in (
        str,
        int,
        float,
        bool,
        list,
        dict,
        tuple,
        set,
        frozenset,
        type(None),
    )
