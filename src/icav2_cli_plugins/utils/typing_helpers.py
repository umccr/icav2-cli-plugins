#!/usr/bin/env python3

# Typing Function imports
from typing import get_args, get_type_hints, get_origin, Tuple, Any
# Typing Hint imports
from typing import Optional, Union, List
# Object inspection
from inspect import isclass


def is_optional_type(attr_type: Tuple) -> bool:
    if (
            # Optional[...]
            get_args(attr_type) is not None and
            get_origin(attr_type) is Union and
            hasattr(attr_type, "_name") and
            getattr(attr_type, "_name") == "Optional"
    ) or (
            # Optional[Union[...]]
            any(
                map(
                    lambda arg_type_iter: (
                            isclass(arg_type_iter) and
                            issubclass(arg_type_iter, type(None))
                    ),
                    get_args(attr_type)
                )
            )
    ):
        return True
    return False


def is_list_type(attr_type):
    if (
            # List[...]
            get_args(attr_type) is not None and
            isclass(get_origin(attr_type)) and
            issubclass(get_origin(attr_type), List)
    ):
        return True
    return False


def is_union(attr_type) -> bool:
    if (
            # Union[...]
            get_args(attr_type) is not None and
            get_origin(attr_type) is Union
    ) or (
            # Might already be a tuple if originated from
            # Optional[Union[...]]
            isinstance(attr_type, Tuple)
    ):
        return True
    return False


def strip_optional_type(attr_type) -> Union[Tuple, Any]:
    non_optional_tuples = tuple(
        filter(
            lambda arg_iter: not (isclass(arg_iter) and issubclass(arg_iter, type(None))),
            get_args(attr_type)
        )
    )

    if len(non_optional_tuples) == 1:
        return non_optional_tuples[0]
    return non_optional_tuples


def strip_list_type(attr_type) -> Union[Tuple, Any]:
    tuple_args = get_args(attr_type)

    if len(tuple_args) == 1:
        return tuple_args[0]
    return tuple_args


def strip_union_type(attr_type) -> Union[Tuple, Any]:
    # Only need to strip if not a tuple type
    if isinstance(attr_type, Tuple):
        return attr_type

    tuple_args = get_args(attr_type)

    if len(tuple_args) == 1:
        return tuple_args[0]
    return tuple_args


def get_args_from_arg_list_type(arg_type) -> Tuple[Any, bool]:
    # Top is list
    if is_list_type(arg_type):
        return get_args(arg_type)[0], True
    return arg_type, False


def is_multi_type(arg_type) -> bool:
    if isinstance(arg_type, Tuple):
        return True
    if hasattr(arg_type, "__origin__") and arg_type.__origin__ == Union:
        return True
    return False


def split_multi_type(arg_type) -> Tuple:
    if isinstance(arg_type, Tuple):
        return arg_type
    return get_args(arg_type)
