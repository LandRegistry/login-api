import os

logging_config_file_path = os.environ['LOGGING_CONFIG_FILE_PATH']

CONFIG_DICT = {
    'DEBUG': False,
    'LOGGING_CONFIG_FILE_PATH': logging_config_file_path,
    'SQLALCHEMY_DATABASE_URI': os.environ['SQLALCHEMY_DATABASE_URI'],
    'PASSWORD_SALT': os.environ['PASSWORD_SALT'],
    'PORT': os.environ['PORT'],
}

settings = os.environ.get('SETTINGS')

if settings == 'dev':
    CONFIG_DICT['DEBUG'] = True
elif settings == 'test':
    CONFIG_DICT['DEBUG'] = True
    CONFIG_DICT['TESTING'] = True
