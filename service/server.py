# !/usr/bin/env python
import os
import json
import logging
import logging.config
from flask import request, Response, Flask
from flask_sqlalchemy import SQLAlchemy
from service import security, setup_logging
from service.db_access import DBAccess

AUTH_FAILURE_RESPONSE_BODY = json.dumps({'error': 'Invalid credentials'})
INVALID_REQUEST_RESPONSE_BODY = json.dumps({'error': 'Invalid request'})
INTERNAL_SERVER_ERROR_RESPONSE_BODY = json.dumps({'error': 'Internal server error'})
JSON_CONTENT_TYPE = 'application/json'

INVALID_REQUEST_RESPONSE = Response(INVALID_REQUEST_RESPONSE_BODY, status=400, mimetype=JSON_CONTENT_TYPE)
USER_NOT_FOUND_RESPONSE = Response(json.dumps({'error': 'User not found'}), status=404, mimetype=JSON_CONTENT_TYPE)

app = Flask(__name__)

LOGGER = logging.getLogger(__name__)

@app.errorhandler(Exception)
def handleServerError(error):
    LOGGER.error('An error occurred when processing a request', exc_info = error)
    return Response(INTERNAL_SERVER_ERROR_RESPONSE_BODY, status=500, mimetype=JSON_CONTENT_TYPE)

@app.route('/user/authenticate', methods=['POST'])
def authenticate_user():
    request_json = _try_get_request_json(request)

    if request_json and _is_auth_request_data_valid(request_json):
        credentials = request_json['credentials']
        user_id = credentials['user_id']
        password = credentials['password']
        password_hash = security.get_user_password_hash(user_id, password, app.config['PASSWORD_SALT'])
        user = db_access.get_user(user_id, password_hash)
        
        if user:
            return Response(_authenticated_response_body(user), mimetype=JSON_CONTENT_TYPE)
        else:
            return Response(AUTH_FAILURE_RESPONSE_BODY, status=401, mimetype=JSON_CONTENT_TYPE)
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
        password_hash = security.get_user_password_hash(user_id, password, app.config['PASSWORD_SALT'])
        if db_access.create_user(user_id, password_hash):
            LOGGER.info('Created user {}'.format(user_id))
            return Response(json.dumps({'created': True}), mimetype=JSON_CONTENT_TYPE)
        else:
            return Response(json.dumps({'error': 'User already exists'}), 409, mimetype=JSON_CONTENT_TYPE)
    else:
        return INVALID_REQUEST_RESPONSE

@app.route('/admin/user/<user_id>/update', methods=['POST'])
def update_user(user_id):
    request_json = _try_get_request_json(request)
    if request_json and _is_update_request_data_valid(request_json):
        new_password = request_json['user']['password']
        new_password_hash = security.get_user_password_hash(user_id, new_password, app.config['PASSWORD_SALT'])
        if db_access.update_user(user_id=user_id, password_hash=new_password_hash):
            LOGGER.info('Updated user {}'.format(user_id))
            return Response(json.dumps({'updated': True}), mimetype=JSON_CONTENT_TYPE)
        else:
            return USER_NOT_FOUND_RESPONSE
    else:
        return INVALID_REQUEST_RESPONSE
        

@app.route('/admin/user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    if db_access.delete_user(user_id):
        LOGGER.info('Deleted user {}'.format(user_id))
        return Response(json.dumps({'deleted': True}), mimetype=JSON_CONTENT_TYPE)
    else:
        return USER_NOT_FOUND_RESPONSE

def _try_get_request_json(request):
    try:
        return request.get_json()
    except Exception as e:
        LOGGER.error('Failed to parse JSON body from request', exc_info = e)
        return None
    
def _is_auth_request_data_valid(request_data):
    credentials = request_data.get('credentials')
    return credentials and credentials.get('user_id') and credentials.get('password')

def _is_create_request_data_valid(request_data):
    user = request_data.get('user')
    return user and user.get('user_id') and user.get('password')

def _is_update_request_data_valid(request_data):
    user = request_data.get('user')
    return user and user.get('password')

def _authenticated_response_body(user):
    return json.dumps({"user": {"user_id": user.user_id}})

def run_app():
    from config import CONFIG_DICT
    app.config.update(CONFIG_DICT)
    setup_logging(app.config['LOGGING_CONFIG_FILE_PATH'])
    db = SQLAlchemy(app)
    global db_access
    db_access = DBAccess(db)
    port = int(app.config.get('PORT', 8005))
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':    
    run_app()
