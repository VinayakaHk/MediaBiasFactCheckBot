"""
This type stub file was generated by pyright.
"""

import praw.models
from typing import Any, Iterator, TYPE_CHECKING
from ....util.cache import cachedproperty
from ...base import PRAWBase
from .base import BaseListingMixin
from .gilded import GildedListingMixin
from .rising import RisingListingMixin

"""Provide the SubredditListingMixin class."""
if TYPE_CHECKING:
    ...
class CommentHelper(PRAWBase):
    """Provide a set of functions to interact with a :class:`.Subreddit`'s comments."""
    def __call__(self, **generator_kwargs: str | int | dict[str, str]) -> Iterator[praw.models.Comment]:
        """Return a :class:`.ListingGenerator` for the :class:`.Subreddit`'s comments.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        This method should be used in a way similar to the example below:

        .. code-block:: python

            for comment in reddit.subreddit("test").comments(limit=25):
                print(comment.author)

        """
        ...
    
    def __init__(self, subreddit: praw.models.Subreddit | SubredditListingMixin) -> None:
        """Initialize a :class:`.CommentHelper` instance."""
        ...
    


class SubredditListingMixin(BaseListingMixin, GildedListingMixin, RisingListingMixin):
    """Adds additional methods pertaining to subreddit-like instances."""
    @cachedproperty
    def comments(self) -> CommentHelper:
        """Provide an instance of :class:`.CommentHelper`.

        For example, to output the author of the 25 most recent comments of r/test
        execute:

        .. code-block:: python

            for comment in reddit.subreddit("test").comments(limit=25):
                print(comment.author)

        """
        ...
    
    def __init__(self, reddit: praw.Reddit, _data: dict[str, Any] | None) -> None:
        """Initialize a :class:`.SubredditListingMixin` instance.

        :param reddit: An instance of :class:`.Reddit`.

        """
        ...
    


