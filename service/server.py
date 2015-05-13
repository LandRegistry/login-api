# !/usr/bin/env python
import os
import json
import logging
import logging.config
from flask import request, Response
from service import app, db_access, security


AUTH_FAILURE_RESPONSE_BODY = json.dumps({'error': 'Invalid credentials'})
INVALID_REQUEST_RESPONSE_BODY = json.dumps({'error': 'Invalid request'})
INTERNAL_SERVER_ERROR_RESPONSE_BODY = json.dumps(
    {'error': 'Internal server error'}
)
JSON_CONTENT_TYPE = 'application/json'

INVALID_REQUEST_RESPONSE = Response(
    INVALID_REQUEST_RESPONSE_BODY,
    status=400,
    mimetype=JSON_CONTENT_TYPE
)
USER_NOT_FOUND_RESPONSE = Response(
    json.dumps({'error': 'User not found'}),
    status=404,
    mimetype=JSON_CONTENT_TYPE
)


MAX_LOGIN_ATTEMPTS = 10

LOGGER = logging.getLogger(__name__)


@app.errorhandler(Exception)
def handleServerError(error):
    LOGGER.error(
        'An error occurred when processing a request',
        exc_info=error
    )
    return Response(
        INTERNAL_SERVER_ERROR_RESPONSE_BODY,
        status=500,
        mimetype=JSON_CONTENT_TYPE
    )


@app.route('/', methods=['GET'])
def healthcheck():
    return "OK"


@app.route('/user/authenticate', methods=['POST'])
def authenticate_user():
    request_json = _try_get_request_json(request)

    if request_json and _is_auth_request_data_valid(request_json):
        credentials = request_json['credentials']
        user_id = credentials['user_id']
        password = credentials['password']
        password_hash = security.get_user_password_hash(
            user_id,
            password,
            app.config['PASSWORD_SALT']
        )

        # Find how many failed logins the users has since last successful login
        failed_login_attempts = db_access.get_failed_logins(user_id)

        # If they have less attempts than the limit try to authorise
        skip_authorise = (
            failed_login_attempts is None or
            failed_login_attempts >= MAX_LOGIN_ATTEMPTS
        )
        if not skip_authorise:
            user = db_access.get_user(user_id, password_hash)
            if user:
                # Reset failed login attempts to zero and proceed
                db_access.update_failed_logins(user_id, 0)
                return Response(
                    _authenticated_response_body(user),
                    mimetype=JSON_CONTENT_TYPE
                )

        log_msg = ('Too many bad logins' if skip_authorise
                   else 'Invalid credentials used')
        LOGGER.info('{}. username: {}, attempt: {}.'.format(
            log_msg,
            user_id,
            failed_login_attempts
        ))
        # If user was found failed_login_attempts will be an int, else None
        if failed_login_attempts is not None:
            # Increment the number of failed login attempts
            failed_login_attempts += 1
            db_access.update_failed_logins(user_id, failed_login_attempts)
        return Response(
            AUTH_FAILURE_RESPONSE_BODY,
            status=401,
            mimetype=JSON_CONTENT_TYPE
        )
    else:
        return INVALID_REQUEST_RESPONSE


@app.route('/admin/user', methods=['POST'])
def create_user():
    request_json = _try_get_request_json(request)
    if request_json and _is_create_request_data_valid(request_json):
        user = request_json['user']
        user_id = user['user_id']
        password = user['password']
        # TODO: common code
        password_hash = security.get_user_password_hash(
            user_id,
            password,
            app.config['PASSWORD_SALT']
        )
        if db_access.create_user(user_id, password_hash):
            LOGGER.info('Created user {}'.format(user_id))
            return Response(
                json.dumps({'created': True}),
                mimetype=JSON_CONTENT_TYPE
            )
        else:
            return Response(
                json.dumps({'error': 'User already exists'}),
                409,
                mimetype=JSON_CONTENT_TYPE
            )
    else:
        return INVALID_REQUEST_RESPONSE


@app.route('/admin/user/<user_id>/update', methods=['POST'])
def update_user(user_id):
    request_json = _try_get_request_json(request)
    if request_json and _is_update_request_data_valid(request_json):
        new_password = request_json['user']['password']
        new_password_hash = security.get_user_password_hash(
            user_id,
            new_password,
            app.config['PASSWORD_SALT']
        )
        if db_access.update_user(
            user_id=user_id,
            password_hash=new_password_hash
        ):
            LOGGER.info('Updated user {}'.format(user_id))
            return Response(
                json.dumps({'updated': True}),
                mimetype=JSON_CONTENT_TYPE
            )
        else:
            return USER_NOT_FOUND_RESPONSE
    else:
        return INVALID_REQUEST_RESPONSE


@app.route('/admin/user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    if db_access.delete_user(user_id):
        LOGGER.info('Deleted user {}'.format(user_id))
        return Response(
            json.dumps({'deleted': True}),
            mimetype=JSON_CONTENT_TYPE
        )
    else:
        return USER_NOT_FOUND_RESPONSE


@app.route('/admin/user/<user_id>/unlock-account')
def unlock_account(user_id):
    if db_access.update_failed_logins(user_id, 0):
        LOGGER.info('Reset failed login attempts for user {}'.format(user_id))
        return Response(json.dumps({'reset': True}),
                        mimetype=JSON_CONTENT_TYPE)
    else:
        return USER_NOT_FOUND_RESPONSE


@app.route('/admin/user/<user_id>/get-failed-logins')
def get_failed_logins(user_id):
    failed_logins = db_access.get_failed_logins(user_id)
    if failed_logins is not None:
        LOGGER.info('Get failed login attempts for user {}'.format(user_id))
        resp_json = json.dumps({'failed_login_attempts': failed_logins})
        return Response(resp_json, mimetype=JSON_CONTENT_TYPE)
    else:
        return USER_NOT_FOUND_RESPONSE


def _try_get_request_json(request):
    try:
        return request.get_json()
    except Exception as e:
        LOGGER.error('Failed to parse JSON body from request', exc_info=e)
        return None


def _is_auth_request_data_valid(request_data):
    credentials = request_data.get('credentials')
    if credentials:
        user_id = credentials.get('user_id', None)
        user_password = credentials.get('password', None)
        return user_id and user_password
    return False


def _is_create_request_data_valid(request_data):
    user = request_data.get('user')
    return user and user.get('user_id') and user.get('password')


def _is_update_request_data_valid(request_data):
    user = request_data.get('user')
    return user and user.get('password')


def _authenticated_response_body(user):
    return json.dumps({"user": {"user_id": user.user_id}})


def run_app():
    port = int(app.config.get('PORT', 8005))
    app.run(host='0.0.0.0', port=port)
