import logging
from logging import config
import json

def setup_logging(logging_config_file_path):
    try:
        with open(logging_config_file_path, 'rt') as file:
            config = json.load(file)
        logging.config.dictConfig(config)
    except IOError as e:
        raise (Exception('Failed to load logging configuration', e))
