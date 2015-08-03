import atexit
import logging
from service.server import run_app

LOGGER = logging.getLogger(__name__)


@atexit.register
def handle_shutdown(*args, **kwargs):
    LOGGER.info('Stopped the server')

LOGGER.info('Starting the server')
run_app()
