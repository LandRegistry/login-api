from collections import namedtuple
import json
from mock import MagicMock, call, patch

from service import server
from service.security import get_user_password_hash
from service.server import app


AUTHENTICATE_ROUTE = '/user/authenticate'
CREATE_USER_ROUTE = '/admin/user'
UPDATE_USER_ROUTE_FORMAT = '/admin/user/{}/update'
DELETE_USER_ROUTE_FORMAT = '/admin/user/{}'
UNLOCK_ACCOUNT_ROUTE_FORMAT = 'admin/user/{}/unlock-account'
GET_FAILED_LOGINS_ROUTE_FORMAT = 'admin/user/{}/get-failed-logins'
HEALTH_ROUTE = '/health'

JSON_CONTENT_TYPE_HEADER = {"Content-type": "application/json"}

INTERNAL_SERVER_ERROR_RESPONSE_BODY = '{"error": "Internal server error"}'
INVALID_REQUEST_RESPONSE_BODY = '{"error": "Invalid request"}'
UPDATED_USER_RESPONSE_BODY = '{"updated": true}'
DELETED_USER_RESPONSE_BODY = '{"deleted": true}'
INVALID_CREDENTIALS_RESPONSE_BODY = '{"error": "Invalid credentials"}'
USER_ALREADY_EXISTS_RESPONSE_BODY = '{"error": "User already exists"}'
CREATED_USER_RESPONSE_BODY = '{"created": true}'
USER_NOT_FOUND_RESPONSE_BODY = '{"error": "User not found"}'
GET_FAILED_LOGINS_RESPONSE_BODY_FORMAT = '{{"failed_login_attempts": {}}}'
UNLOCK_ACCOUNT_RESPONSE_BODY = '{"reset": true}'

FakeUser = namedtuple('User', ['user_id', 'password_hash', 'failed_logins'])


class TestServer:

    def setup_method(self, method):
        config_dict = {
            'DEBUG': False,
            'PASSWORD_SALT': 'salt',
        }

        app.config.update(config_dict)
        mock_db_access = MagicMock()
        mock_db_access.get_user.return_value = None
        server.db_access = mock_db_access
        self.app = app.test_client()

    def test_authenticate_user_returns_400_response_when_empty_body(self):
        response = self.app.post(
            AUTHENTICATE_ROUTE,
            headers=JSON_CONTENT_TYPE_HEADER
        )
        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_authenticate_user_returns_400_when_body_is_not_json(self):
        response = self.app.post(
            AUTHENTICATE_ROUTE,
            data='Not a JSON body',
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_authenticate_user_returns_400_when_credentials_missing(self):
        response = self.app.post(
            AUTHENTICATE_ROUTE,
            data='{"valid": "json", "but": "no credentials"}',
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_authenticate_user_returns_400_response_when_user_id_missing(self):
        response = self.app.post(
            AUTHENTICATE_ROUTE,
            data='{"credentials": {"password":"somepassword"}}',
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_authenticate_user_returns_400_response_when_user_id_empty(self):
        response = self.app.post(
            AUTHENTICATE_ROUTE,
            data='{"credentials": {"user_id": "", "password":"somepassword"}}',
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_authenticate_user_returns_400_when_password_missing(self):
        response = self.app.post(
            AUTHENTICATE_ROUTE,
            data='{"credentials": {"user_id": "userid"}}',
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_authenticate_user_returns_400_response_when_password_empty(self):
        response = self.app.post(
            AUTHENTICATE_ROUTE,
            data='{"credentials": {"user_id": "userid", "password": ""}}',
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_authenticate_user_returns_400_when_contentheader_not_set(self):
        wrong_content_type_header = {
            "Content-type": "application/x-www-form-urlencoded"
        }
        valid_body = '''{
            "credentials": {"user_id": "userid", "password": "somepassword"}
        }'''
        response = self.app.post(
            AUTHENTICATE_ROUTE,
            data=valid_body,
            headers=wrong_content_type_header
        )

        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_authenticate_user_returns_401_when_credentials_not_in_db(self):
        body = '''{
            "credentials": {"user_id": "userid", "password": "somepassword"}
        }'''

        mock_db_access = MagicMock()
        mock_db_access.get_user = lambda self, *args, **kwargs: None
        mock_db_access.get_failed_logins = lambda self, *args, **kwargs: None
        mock_db_access.update_failed_logins = lambda self, *args, **kwargs: 1
        server.db_access = mock_db_access

        response = self.app.post(
            AUTHENTICATE_ROUTE,
            data=body,
            headers=JSON_CONTENT_TYPE_HEADER
        )
        assert response.status_code == 401
        assert response.data.decode() == INVALID_CREDENTIALS_RESPONSE_BODY

    def test_authenticate_user_returns_401_if_failed_login_exceeds_limit(self):
        body = '''{
            "credentials": {"user_id": "userid", "password": "somepassword"}
        }'''

        mock_db_access = MagicMock()
        mock_db_access.get_user = FakeUser('user_id', 'passwordhash', 20)
        mock_db_access.get_failed_logins = lambda self, *args, **kwargs: 20
        mock_db_access.update_failed_logins = lambda self, *args, **kwargs: 1
        server.db_access = mock_db_access

        response = self.app.post(
            AUTHENTICATE_ROUTE,
            data=body,
            headers=JSON_CONTENT_TYPE_HEADER
        )
        assert response.status_code == 401
        assert response.data.decode() == INVALID_CREDENTIALS_RESPONSE_BODY

    def test_authenticate_user_returns_500_response_when_error_occurs(self):
        valid_body = '''{
            "credentials": {"user_id": "userid1", "password": "somepassword"}
        }'''

        def failing_get_user(s, *args, **kwargs):
            raise Exception('Intentional test exception')

        mock_db_access = MagicMock()
        mock_db_access.get_user = failing_get_user
        server.db_access = mock_db_access

        response = self.app.post(
            AUTHENTICATE_ROUTE,
            data=valid_body,
            headers=JSON_CONTENT_TYPE_HEADER
        )
        assert response.status_code == 500
        assert response.data.decode() == INTERNAL_SERVER_ERROR_RESPONSE_BODY

    def test_authenticate_user_calls_db_access_to_find_user(self):
        user_id = 'userid1'
        password = 'somepassword'
        body_format = '{"credentials": {"user_id": "%s", "password": "%s"}}'
        valid_body = body_format % (user_id, password)

        mock_db_access = MagicMock()
        mock_db_access.get_user.return_value = FakeUser(
            user_id,
            'passwordhash',
            0
        )
        mock_db_access.get_failed_logins = lambda self, *args, **kwargs: 0
        mock_db_access.update_failed_logins = lambda self, *args, **kwargs: 1
        server.db_access = mock_db_access

        self.app.post(
            AUTHENTICATE_ROUTE,
            data=valid_body,
            headers=JSON_CONTENT_TYPE_HEADER
        )

        expected_password_hash_to_pass = get_user_password_hash(
            user_id,
            password,
            app.config['PASSWORD_SALT']
        )
        mock_db_access.get_user.assert_called_once_with(
            user_id,
            expected_password_hash_to_pass
        )

    def test_authenticate_user_returns_200_when_credentials_are_valid(self):
        valid_body = '''{
            "credentials": {"user_id": "userid1", "password": "somepassword"}
        }'''

        mock_db_access = MagicMock()
        mock_db_access.get_user.return_value = FakeUser(
            'userid1',
            'passwordhash',
            0
        )
        mock_db_access.get_failed_logins = lambda self, *args, **kwargs: 0
        mock_db_access.update_failed_logins = lambda self, *args, **kwargs: 1
        server.db_access = mock_db_access

        response = self.app.post(
            AUTHENTICATE_ROUTE,
            data=valid_body,
            headers=JSON_CONTENT_TYPE_HEADER
        )
        assert response.status_code == 200
        assert response.data.decode() == '{"user": {"user_id": "userid1"}}'

    def test_create_user_returns_400_response_when_empty_body(self):
        response = self.app.post(CREATE_USER_ROUTE)
        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_create_user_returns_400_response_when_body_is_not_json(self):
        response = self.app.post(
            CREATE_USER_ROUTE,
            data='Not a JSON body',
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_create_user_returns_400_response_when_user_missing(self):
        response = self.app.post(
            CREATE_USER_ROUTE,
            data='{"valid": "json", "but": "no user"}',
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_create_user_returns_400_response_when_user_id_missing(self):
        response = self.app.post(
            CREATE_USER_ROUTE,
            data='{"user": {"password":"somepassword"}}',
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_create_user_returns_400_response_when_user_id_empty(self):
        response = self.app.post(
            CREATE_USER_ROUTE,
            data='{"user": {"user_id": "", "password":"somepassword"}}',
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_create_user_returns_400_response_when_user_password_missing(self):
        response = self.app.post(
            CREATE_USER_ROUTE,
            data='{"user": {"user_id" : "userid"}}',
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_create_user_returns_400_response_when_password_empty(self):
        response = self.app.post(
            CREATE_USER_ROUTE,
            data='{"user": {"user_id" : "userid", "password": ""}}',
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_create_user_returns_400_when_json_content_header_not_set(self):
        wrong_content_type_header = {
            "Content-type": "application/x-www-form-urlencoded"
        }
        valid_body = '''{
            "user": {"user_id": "userid", "password": "somepassword"}
        }'''
        response = self.app.post(
            CREATE_USER_ROUTE,
            data=valid_body,
            headers=wrong_content_type_header
        )

        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_create_user_calls_db_access_to_create_user(self):
        user_id = 'userid1'
        password = 'somepassword'
        valid_body_format = '{"user": {"user_id": "%s", "password": "%s"}}'
        valid_body = valid_body_format % (user_id, password)

        mock_db_access = MagicMock()
        mock_db_access.create_user.return_value = True
        server.db_access = mock_db_access

        self.app.post(
            CREATE_USER_ROUTE,
            data=valid_body,
            headers=JSON_CONTENT_TYPE_HEADER
        )

        expected_password_hash_to_pass = get_user_password_hash(
            user_id,
            password,
            app.config['PASSWORD_SALT']
        )
        mock_db_access.create_user.assert_called_once_with(
            user_id,
            expected_password_hash_to_pass
        )

    def test_create_user_returns_409_response_when_user_already_exists(self):
        valid_body = '''{"user": {
            "user_id": "userid1", "password": "somepassword"
        }}'''

        mock_db_access = MagicMock()
        mock_db_access.create_user.return_value = False
        server.db_access = mock_db_access

        response = self.app.post(
            CREATE_USER_ROUTE,
            data=valid_body,
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 409
        assert response.data.decode() == USER_ALREADY_EXISTS_RESPONSE_BODY

    def test_create_user_returns_200_when_user_creation_successful(self):
        valid_body = '''{"user": {
            "user_id": "userid1", "password": "somepassword"
        }}'''

        mock_db_access = MagicMock()
        mock_db_access.create_user.return_value = True
        server.db_access = mock_db_access

        response = self.app.post(
            CREATE_USER_ROUTE,
            data=valid_body,
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 200
        assert response.data.decode() == CREATED_USER_RESPONSE_BODY

    def test_create_user_returns_500_response_when_an_error_occurs(self):
        valid_body = '''{"user": {
            "user_id": "userid1",
            "password": "somepassword"
        }}'''

        def failing_create_user(s, *args, **kwargs):
            raise Exception('Intentional test exception')

        mock_db_access = MagicMock()
        mock_db_access.create_user = failing_create_user
        server.db_access = mock_db_access

        response = self.app.post(
            CREATE_USER_ROUTE,
            data=valid_body,
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 500
        assert response.data.decode() == INTERNAL_SERVER_ERROR_RESPONSE_BODY

    def test_update_user_returns_400_response_when_empty_body(self):
        response = self.app.post(
            UPDATE_USER_ROUTE_FORMAT.format("userid"),
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_update_user_returns_400_response_when_body_is_not_json(self):
        response = self.app.post(
            UPDATE_USER_ROUTE_FORMAT.format("userid"),
            data='Not a JSON body',
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_update_user_returns_400_response_when_user_missing(self):
        response = self.app.post(
            UPDATE_USER_ROUTE_FORMAT.format("userid"),
            data='{"valid": "json", "but": "no user"}',
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_update_user_returns_400_response_when_user_password_missing(self):
        response = self.app.post(
            UPDATE_USER_ROUTE_FORMAT.format("userid"),
            data='{"user": { }}',
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_update_user_returns_400_response_when_password_empty(self):
        response = self.app.post(
            UPDATE_USER_ROUTE_FORMAT.format("userid"),
            data='{"user": { "password": "" }}',
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_update_user_returns_400_when_json_content_header_not_set(self):
        wrong_content_type_header = {
            "Content-type": "application/x-www-form-urlencoded"
        }
        valid_body = '{"user": {"password": "somepassword"}}'

        response = self.app.post(
            UPDATE_USER_ROUTE_FORMAT.format("userid"),
            data=valid_body,
            headers=wrong_content_type_header
        )

        assert response.status_code == 400
        assert response.data.decode() == INVALID_REQUEST_RESPONSE_BODY

    def test_update_user_calls_db_access_to_update_user(self):
        user_id = 'userid1'
        password = 'somepassword'
        valid_body = '{"user": {"password": "%s"}}' % (password)

        mock_db_access = MagicMock()
        mock_db_access.update_user.return_value = 1
        server.db_access = mock_db_access

        self.app.post(
            UPDATE_USER_ROUTE_FORMAT.format(user_id),
            data=valid_body,
            headers=JSON_CONTENT_TYPE_HEADER
        )

        expected_password_hash_to_pass = get_user_password_hash(
            user_id,
            password,
            app.config['PASSWORD_SALT']
        )
        mock_db_access.update_user.assert_called_once_with(
            user_id=user_id,
            password_hash=expected_password_hash_to_pass
        )

    def test_update_user_returns_404_response_when_user_not_found(self):
        valid_body = '{"user": {"password": "somepassword"}}'

        mock_db_access = MagicMock()
        mock_db_access.update_user.return_value = 0
        server.db_access = mock_db_access

        response = self.app.post(
            UPDATE_USER_ROUTE_FORMAT.format('userid1'),
            data=valid_body,
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 404
        assert response.data.decode() == USER_NOT_FOUND_RESPONSE_BODY

    def test_update_user_returns_200_when_user_update_successful(self):
        valid_body = '{"user": {"password": "somepassword"}}'

        mock_db_access = MagicMock()
        mock_db_access.update_user.return_value = 1
        server.db_access = mock_db_access

        response = self.app.post(
            UPDATE_USER_ROUTE_FORMAT.format('userid1'),
            data=valid_body,
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 200
        assert response.data.decode() == UPDATED_USER_RESPONSE_BODY

    def test_update_user_returns_500_response_when_an_error_occurs(self):
        valid_body = '{"user": {"password": "somepassword"}}'

        def failing_update_user(s, *args, **kwargs):
            raise Exception('Intentional test exception')

        mock_db_access = MagicMock()
        mock_db_access.update_user = failing_update_user
        server.db_access = mock_db_access

        response = self.app.post(
            UPDATE_USER_ROUTE_FORMAT.format("userid1"),
            data=valid_body,
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert response.status_code == 500
        assert response.data.decode() == INTERNAL_SERVER_ERROR_RESPONSE_BODY

    def test_delete_user_calls_db_access_to_delete_user(self):
        user_id = 'userid1'

        mock_db_access = MagicMock()
        mock_db_access.delete_user.return_value = 1
        server.db_access = mock_db_access

        self.app.delete(DELETE_USER_ROUTE_FORMAT.format(user_id))

        mock_db_access.delete_user.assert_called_once_with(user_id)

    def test_delete_user_returns_404_response_when_user_not_found(self):
        user_id = 'userid1'

        mock_db_access = MagicMock()
        mock_db_access.delete_user.return_value = 0
        server.db_access = mock_db_access

        response = self.app.delete(DELETE_USER_ROUTE_FORMAT.format(user_id))

        assert response.status_code == 404
        assert response.data.decode() == USER_NOT_FOUND_RESPONSE_BODY

    def test_delete_user_returns_200_when_user_deletion_successful(self):
        user_id = 'userid1'

        mock_db_access = MagicMock()
        mock_db_access.delete_user.return_value = 1
        server.db_access = mock_db_access

        response = self.app.delete(DELETE_USER_ROUTE_FORMAT.format(user_id))

        assert response.status_code == 200
        assert response.data.decode() == DELETED_USER_RESPONSE_BODY

    def test_delete_user_returns_500_response_when_an_error_occurs(self):
        user_id = 'userid1'

        def failing_delete_user(s, *args, **kwargs):
            raise Exception('Intentional test exception')

        mock_db_access = MagicMock()
        mock_db_access.delete_user = failing_delete_user
        server.db_access = mock_db_access

        response = self.app.delete(DELETE_USER_ROUTE_FORMAT.format(user_id))

        assert response.status_code == 500
        assert response.data.decode() == INTERNAL_SERVER_ERROR_RESPONSE_BODY

    def test_get_failed_logins_calls_db_access_to_get_failed_login_count(self):
        user_id = 'userid1'

        mock_db_access = MagicMock()
        mock_db_access.get_failed_logins.return_value = 2
        server.db_access = mock_db_access

        self.app.get(GET_FAILED_LOGINS_ROUTE_FORMAT.format(user_id))

        mock_db_access.get_failed_logins.assert_called_once_with(user_id)

    def test_get_failed_logins_returns_404_response_when_user_not_found(self):
        user_id = 'userid1'

        mock_db_access = MagicMock()
        mock_db_access.get_failed_logins.return_value = None
        server.db_access = mock_db_access

        response = self.app.get(GET_FAILED_LOGINS_ROUTE_FORMAT.format(user_id))

        assert response.status_code == 404
        assert response.data.decode() == USER_NOT_FOUND_RESPONSE_BODY

    def test_get_failed_logins_returns_200_when_failed_logins_retrieved(self):
        user_id = 'userid1'

        failed_logins = 2

        mock_db_access = MagicMock()
        mock_db_access.get_failed_logins.return_value = failed_logins
        server.db_access = mock_db_access

        response = self.app.get(GET_FAILED_LOGINS_ROUTE_FORMAT.format(user_id))

        assert response.status_code == 200
        expected = GET_FAILED_LOGINS_RESPONSE_BODY_FORMAT.format(
            failed_logins
        )

        assert response.data.decode() == expected

    def test_unlock_account_calls_db_access_to_reset_failed_logins(self):
        user_id = 'userid1'

        mock_db_access = MagicMock()
        mock_db_access.update_failed_logins.return_value = 1
        server.db_access = mock_db_access

        self.app.get(UNLOCK_ACCOUNT_ROUTE_FORMAT.format(user_id))

        mock_db_access.update_failed_logins.assert_called_once_with(user_id, 0)

    def test_unlock_account_returns_404_response_when_user_not_found(self):
        user_id = 'userid1'

        mock_db_access = MagicMock()
        mock_db_access.update_failed_logins.return_value = 0
        server.db_access = mock_db_access

        response = self.app.get(UNLOCK_ACCOUNT_ROUTE_FORMAT.format(user_id))

        assert response.status_code == 404
        assert response.data.decode() == USER_NOT_FOUND_RESPONSE_BODY

    def test_unlock_account_returns_200_when_failed_logins_reset(self):
        user_id = 'userid1'

        mock_db_access = MagicMock()
        mock_db_access.update_failed_logins.return_value = 1
        server.db_access = mock_db_access

        response = self.app.get(UNLOCK_ACCOUNT_ROUTE_FORMAT.format(user_id))

        assert response.status_code == 200
        assert response.data.decode() == UNLOCK_ACCOUNT_RESPONSE_BODY

    @patch('service.server.db_access.get_user', return_value=None)
    def test_health_returns_200_response_when_db_responds_properly(self, mock_get_user):
        response = self.app.get(HEALTH_ROUTE)
        assert response.status_code == 200
        assert response.data.decode() == '{"status": "ok"}'

    @patch('service.server.db_access.get_user', side_effect=Exception('Test exception'))
    def test_health_returns_500_response_when_db_access_fails(self, mock_get_user):
        response = self.app.get(HEALTH_ROUTE)

        assert response.status_code == 500
        json_response = json.loads(response.data.decode())
        assert json_response == {
            'status': 'error',
            'errors': ['Problem talking to PostgreSQL: Test exception'],
        }
