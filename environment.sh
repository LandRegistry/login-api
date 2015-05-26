#!/bin/sh

export SETTINGS='dev'
export LOGGING_CONFIG_FILE_PATH=logging_config.json
export FAULT_LOG_FILE_PATH='/var/log/applications/login-api-fault.log'
export SQLALCHEMY_DATABASE_URI=postgresql+pg8000://postgres:password@172.16.42.43:5432/user_data
export PASSWORD_SALT=passwordsalt
export PORT=8005
export PYTHONPATH=.
