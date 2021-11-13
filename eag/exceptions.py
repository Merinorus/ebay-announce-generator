

class EbayAnnounceGeneratorException(Exception):
    """
    EbayAnnounceGenerator base exception. Handled at the outermost level.
    All other exception types are subclasses of this exception type.
    """


class AnnounceAlreadyProcessed(EbayAnnounceGeneratorException):
    """
    Requires manual intervention and will stop the bot.
    Most of the time, this is caused by an invalid Configuration.
    """