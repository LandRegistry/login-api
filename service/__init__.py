import faulthandler                      # type: ignore
from flask import Flask                  # type: ignore
from flask_sqlalchemy import SQLAlchemy  # type: ignore

from config import CONFIG_DICT
from service import logging_config
from service import security

# This causes the traceback to be written to the fault log file in case of serious faults
fault_log_file = open(CONFIG_DICT['FAULT_LOG_FILE_PATH'], 'a')
faulthandler.enable(file=fault_log_file)

app = Flask(__name__)
app.config.update(CONFIG_DICT)
db = SQLAlchemy(app)
logging_config.setup_logging()
