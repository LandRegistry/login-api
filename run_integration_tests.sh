#!/bin/bash

source /usr/bin/virtualenvwrapper.sh
workon login-api

source environment.sh
source environment_integration_test.sh

sudo su postgres -c "dropdb test_user_data"
sudo su postgres -c "createdb test_user_data"

python3 manage.py db upgrade

py.test integration_tests/

deactivate