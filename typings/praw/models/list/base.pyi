"""
This type stub file was generated by pyright.
"""

import praw
from typing import Any, Iterator, TYPE_CHECKING
from ..base import PRAWBase

"""Provide the BaseList class."""
if TYPE_CHECKING:
    ...
class BaseList(PRAWBase):
    """An abstract class to coerce a list into a :class:`.PRAWBase`."""
    CHILD_ATTRIBUTE = ...
    def __contains__(self, item: Any) -> bool:
        """Test if item exists in the list."""
        ...
    
    def __getitem__(self, index: int) -> Any:
        """Return the item at position index in the list."""
        ...
    
    def __init__(self, reddit: praw.Reddit, _data: dict[str, Any]) -> None:
        """Initialize a :class:`.BaseList` instance.

        :param reddit: An instance of :class:`.Reddit`.

        """
        ...
    
    def __iter__(self) -> Iterator[Any]:
        """Return an iterator to the list."""
        ...
    
    def __len__(self) -> int:
        """Return the number of items in the list."""
        ...
    
    def __str__(self) -> str:
        """Return a string representation of the list."""
        ...
    


