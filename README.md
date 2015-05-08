# login-api

Login API to authorize users. It is written in Python, with the Flask framework.  

## Setup

To create a virtual env, run the following from a shell:

    mkvirtualenv -p /usr/bin/python3 login-api
    pip install -r requirements.txt

This will also activate the virtual environment for you. You can use
`deactivate` to deactivate it.

Should you need to activate it again (for instance if you are running the app
manually), type:

    workon login-api

## Run the tests

To run the tests for the Login API, go to its folder and run `lr-run-tests`.

## Run the API

Before you run the API, you need to have a PostgreSQL database running  on your development VM
(see `lr-rebuild-all-db-tables` command in the [centos-dev-env](https://github.com/LandRegistry/centos-dev-env) project).

### Run in dev mode

To run the server in dev mode, execute the following command:

    source environment.sh
    python3 run_flask_dev.py

### Run using gunicorn

To run the server using gunicorn, activate your virtual environment, add the application directory to python path
(e.g. `export PYTHONPATH=/vagrant/apps/login-api/:$PYTHONPATH`) and execute the following commands:

    pip install gunicorn
    gunicorn -p /tmp/gunicorn-login-api.pid service.server:app -c gunicorn_settings.py


## Using the endpoints

Below are examples of how to Login API endpoints.

### Authenticating user:

    curl -XPOST http://localhost:8005/user/authenticate -d '{"credentials": {"user_id":"userid123", "password":"password123"}}' -H 'content-type: application/json'

Successful response (HTTP status: 200):

    {"user": {"user_id": "userid123"}}

Unauthorized response (HTTP status: 401)

    {"error": "Invalid credentials"}

### Creating a new user:

    curl -XPOST http://localhost:8005/admin/user -d '{"user": {"user_id":"userid123", "password":"password123"}}' -H 'content-type: application/json'

Successful response (HTTP status: 200):

    {"created": true}

User already exists response (HTTP status: 409):

    {"error": "User already exists"}

### Updating user data (currently just the password):

    curl -XPOST http://localhost:8005/admin/user/userid123/update -d '{"user": {"password":"password321"}}' -H 'content-type: application/json'

Successful response (HTTP status: 200):

    {"updated": true}

User not found response (HTTP status: 404):

    {"error": "User not found"}

### Deleting user:

    curl -XDELETE http://localhost:8005/admin/user/userid123

Successful response (HTTP status: 200):

    {"deleted": true}

User not found response (HTTP status: 404):

    {"error": "User not found"}

### Find failed logins for a user:

    curl -XGET http://localhost:8005/admin/user/userid123/get-failed-logins

Successful response (HTTP status: 200):

    {"failed_login_attempts": 0}

User not found response (HTTP status: 404):

    {"error": "User not found"}

### Unlock user account:

    curl -XGET http://localhost:8005/admin/user/userid123/unlock-account

Successful response (HTTP status: 200):

    {"reset": true}

User not found response (HTTP status: 404):

    {"error": "User not found"}

## Jenkins builds

We use two separate builds:
- [branch](http://52.16.47.1/job/login-api-unit-test%20(Branch)/)
- [master](http://52.16.47.1/job/login-api-unit-test%20(Master)/)

## Database migrations

We use Flask-Migrate (a project which integrates Flask with Alembic, a migration
tool from the author of SQLAlchemy) to handle database migrations. Every time a
model is added or modified, a migration script should be created and committed
to our version control system.

From inside a virtual environment, and after sourcing environment.sh, run the
following to add a new migration script:

    python3 manage.py db migrate -m "add foobar field"

Should you ever need to write a migration script from scratch (to migrate data
for instance) you should use the revision command instead of migrate:

    python3 manage.py db revision -m "do something complicated"

Read Alembic's documentation to learn more.

Once you have a migration script, the next step is to apply it to the database.
To do this run the upgrade command:

    python3 manage.py db upgrade
