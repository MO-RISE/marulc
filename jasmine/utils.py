from typing import Any
from functools import reduce, partial


def deep_get(dikt: dict, *keys: str, default: Any = None) -> Any:
    """A "deep getter" for nested dictionaries

    .. highlight:: python
    .. code-block:: python

        from jasmine.utils import deep_get

        d = {"A": {"B":{"C":"3}}}
        deep_get(d, "A", "B", "C") # Returns 3
        deep_get(d, "A", "B", "C", "D") # Returns None
        deep_get(d, "A", "B", "C", "D", default=89) # Returns 89

    Args:
        dikt (dict): Nested dictionary to operate on
        *keys (str): Any number of keys in descending level in hte nested dictionary.
        default (Any, optional): Default value to return if chain of keys cant be
            followed. Defaults to None.

    Returns:
        Any: The value found at the bottom of the keys or the default value.
    """

    return (
        reduce(
            lambda d, k: d.get(k) if (d and isinstance(d, dict)) else None, keys, dikt
        )
        or default
    )


def filter_on_talker(*talkers: str):
    return partial(filter, lambda item: item.get("Talker") in talkers)


def filter_on_pgn(*PGNs: int):
    return partial(filter, lambda item: item.get("PGN") in PGNs)