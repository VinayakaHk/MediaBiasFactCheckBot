"""
This type stub file was generated by pyright.
"""

import praw
from typing import Any, Iterator, TYPE_CHECKING
from ..base import PRAWBase

"""Provide the ListingGenerator class."""
if TYPE_CHECKING:
    ...
class ListingGenerator(PRAWBase, Iterator):
    """Instances of this class generate :class:`.RedditBase` instances.

    .. warning::

        This class should not be directly utilized. Instead, you will find a number of
        methods that return instances of the class here_.

    .. _here: https://praw.readthedocs.io/en/latest/search.html?q=ListingGenerator

    """
    def __init__(self, reddit: praw.Reddit, url: str, limit: int = ..., params: dict[str, str | int] | None = ...) -> None:
        """Initialize a :class:`.ListingGenerator` instance.

        :param reddit: An instance of :class:`.Reddit`.
        :param url: A URL returning a Reddit listing.
        :param limit: The number of content entries to fetch. If ``limit`` is ``None``,
            then fetch as many entries as possible. Most of Reddit's listings contain a
            maximum of 1000 items, and are returned 100 at a time. This class will
            automatically issue all necessary requests (default: ``100``).
        :param params: A dictionary containing additional query string parameters to
            send with the request.

        """
        ...
    
    def __iter__(self) -> Any:
        """Permit :class:`.ListingGenerator` to operate as an iterator."""
        ...
    
    def __next__(self) -> Any:
        """Permit :class:`.ListingGenerator` to operate as a generator."""
        ...
    


