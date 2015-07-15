import logging

LOGGER = logging.getLogger(__name__)
AUDITING_LOGGER_NAME = __name__


def audit(message):
    LOGGER.info(message)


class ExcludeAuditingFilter(logging.Filter):
    def filter(self, record):
        return not record.name.startswith(AUDITING_LOGGER_NAME)
