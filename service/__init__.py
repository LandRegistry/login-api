import logging
from logging import config
import json
from config import CONFIG_DICT

def setup_logging(logging_config_file_path):
    if CONFIG_DICT['LOGGING']:
        try:
            with open(logging_config_file_path, 'rt') as file:
                config = json.load(file)
            logging.config.dictConfig(config)
        except IOError as e:
            raise (Exception('Failed to load logging configuration', e))
