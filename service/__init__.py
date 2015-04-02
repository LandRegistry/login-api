from config import CONFIG_DICT
from flask import request, Response, Flask
from flask_sqlalchemy import SQLAlchemy
import json
import logging
from logging import config
from service import security


app = Flask(__name__)
app.config.update(CONFIG_DICT)
db = SQLAlchemy(app)


def setup_logging(logging_config_file_path):
    print('LOGGING SETUP')
    print(CONFIG_DICT['LOGGING'])
    if CONFIG_DICT['LOGGING']:
        try:
            with open(logging_config_file_path, 'rt') as file:
                config = json.load(file)
            logging.config.dictConfig(config)
        except IOError as e:
            raise (Exception('Failed to load logging configuration', e))


setup_logging(app.config['LOGGING_CONFIG_FILE_PATH'])
