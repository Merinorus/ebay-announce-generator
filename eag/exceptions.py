

class EAGException(Exception):
    """
    Ebay Announce Generator base exception. Handled at the outermost level.
    All other exception types are subclasses of this exception type.
    """


class AnnounceAlreadyProcessedException(EAGException):
    """
    Announce has most probably been processed already by the bot
    """


class UnknownTemplateException(EAGException):
    """
    A textual description of the announce is expected.
    This exception will be raised when the announce description is more complex than expected
    (eg: contains images).
    """