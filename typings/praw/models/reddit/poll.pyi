"""
This type stub file was generated by pyright.
"""

from typing import Any
from ...util import cachedproperty
from ..base import PRAWBase

"""Provide poll-related classes."""
class PollOption(PRAWBase):
    """Class to represent one option of a poll.

    If ``submission`` is a poll :class:`.Submission`, access the poll's options like so:

    .. code-block:: python

        poll_data = submission.poll_data

        # By index -- print the first option
        print(poll_data.options[0])

        # By ID -- print the option with ID "576797"
        print(poll_data.option("576797"))

    .. include:: ../../typical_attributes.rst

    ============== =================================================
    Attribute      Description
    ============== =================================================
    ``id``         ID of the poll option.
    ``text``       The text of the poll option.
    ``vote_count`` The number of votes the poll option has received.
    ============== =================================================

    """
    def __repr__(self) -> str:
        """Return an object initialization representation of the instance."""
        ...
    
    def __str__(self) -> str:
        """Return a string version of the PollData, its text."""
        ...
    


class PollData(PRAWBase):
    """Class to represent poll data on a poll submission.

    If ``submission`` is a poll :class:`.Submission`, access the poll data like so:

    .. code-block:: python

        poll_data = submission.poll_data
        print(f"There are {poll_data.total_vote_count} votes total.")
        print("The options are:")
        for option in poll_data.options:
            print(f"{option} ({option.vote_count} votes)")
        print(f"I voted for {poll_data.user_selection}.")

    .. include:: ../../typical_attributes.rst

    ======================== =========================================================
    Attribute                Description
    ======================== =========================================================
    ``options``              A list of :class:`.PollOption` of the poll.
    ``total_vote_count``     The total number of votes cast in the poll.
    ``user_selection``       The poll option selected by the authenticated user
                             (possibly ``None``).
    ``voting_end_timestamp`` Time the poll voting closes, represented in `Unix Time`_.
    ======================== =========================================================

    .. _unix time: https://en.wikipedia.org/wiki/Unix_time

    """
    @cachedproperty
    def user_selection(self) -> PollOption | None:
        """Get the user's selection in this poll, if any.

        :returns: The user's selection as a :class:`.PollOption`, or ``None`` if there
            is no choice.

        """
        ...
    
    def __setattr__(self, attribute: str, value: Any): # -> None:
        """Objectify the options attribute, and save user_selection."""
        ...
    
    def option(self, option_id: str) -> PollOption:
        """Get the option with the specified ID.

        :param option_id: The ID of a poll option, as a ``str``.

        :returns: The specified :class:`.PollOption`.

        :raises: :py:class:`KeyError` if no option exists with the specified ID.

        """
        ...
    


