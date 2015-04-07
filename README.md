# login-api

Login API to authorize users. It is written in Python, with the Flask framework.  

### Login API build status

TODO

## Setup

To create a virtual env, run the following from a shell:

    mkvirtualenv -p /usr/bin/python3 login-api
    source environment.sh
    pip install -r requirements.txt

This will also activate the virtual environment for you. You can use
`deactivate` to deactivate it.

Should you need to activate it again (for instance if you are running the app
manually), type:

    workon login-api

## Run the tests

To run the tests for the Login API, go to its folder and run `lr-run-tests`.

## Run the API

Before you run the API, you need to have a PostgreSQL database running  on your development VM (see `db/lr-start-db`
script in the [centos-dev-env](https://github.com/LandRegistry/centos-dev-env) project).

Once you've got it running, execute the following command:

    ./run_flask_dev.py

Make sure you've got permissions to execute that script.

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

TODO
