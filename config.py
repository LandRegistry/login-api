import os

logging_config_file_path = os.environ['LOGGING_CONFIG_FILE_PATH']
fault_log_file_path = os.environ['FAULT_LOG_FILE_PATH']
sqlalchemy_database_uri = os.environ['SQLALCHEMY_DATABASE_URI']
password_salt = os.environ['PASSWORD_SALT']
port = os.environ['PORT']

CONFIG_DICT = {
    'DEBUG': False,
    'LOGGING': True,
    'LOGGING_CONFIG_FILE_PATH': logging_config_file_path,
    'FAULT_LOG_FILE_PATH': fault_log_file_path,
    'SQLALCHEMY_DATABASE_URI': sqlalchemy_database_uri,
    'PASSWORD_SALT': password_salt,
    'PORT': port,
}

settings = os.environ.get('SETTINGS')

if settings == 'dev':
    CONFIG_DICT['DEBUG'] = True
elif settings == 'test':
    CONFIG_DICT['LOGGING'] = False
    CONFIG_DICT['DEBUG'] = True
    CONFIG_DICT['TESTING'] = True
    CONFIG_DICT['FAULT_LOG_FILE_PATH'] = '/dev/null'
