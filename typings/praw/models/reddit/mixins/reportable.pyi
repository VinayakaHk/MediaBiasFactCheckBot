"""
This type stub file was generated by pyright.
"""

"""Provide the ReportableMixin class."""
class ReportableMixin:
    """Interface for :class:`.RedditBase` classes that can be reported."""
    def report(self, reason: str): # -> None:
        """Report this object to the moderators of its subreddit.

        :param reason: The reason for reporting.

        :raises: :class:`.RedditAPIException` if ``reason`` is longer than 100
            characters.

        Example usage:

        .. code-block:: python

            submission = reddit.submission("5or86n")
            submission.report("report reason")

            comment = reddit.comment("dxolpyc")
            comment.report("report reason")

        """
        ...
    


