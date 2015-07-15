from collections import namedtuple
import json
from mock import MagicMock
import mock

from service import server
from service.server import app


AUTHENTICATE_ROUTE = '/user/authenticate'
CREATE_USER_ROUTE = '/admin/user'
UPDATE_USER_ROUTE_FORMAT = '/admin/user/{}/update'
DELETE_USER_ROUTE_FORMAT = '/admin/user/{}'
UNLOCK_ACCOUNT_ROUTE_FORMAT = 'admin/user/{}/unlock-account'
GET_FAILED_LOGINS_ROUTE_FORMAT = 'admin/user/{}/get-failed-logins'
HEALTH_ROUTE = '/health'

JSON_CONTENT_TYPE_HEADER = {"Content-type": "application/json"}

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

    @mock.patch('service.auditing.audit')
    def test_authenticate_user_does_not_audit_when_request_invalid(self, mock_audit):
        self.app.post(
            AUTHENTICATE_ROUTE,
            data='{"invalid": "request"}',
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert mock_audit.mock_calls == []

    @mock.patch('service.auditing.audit')
    def test_authenticate_user_returns_401_when_credentials_not_in_db(self, mock_audit):
        user_id = 'userid'
        body = json.dumps({
            "credentials": {"user_id": user_id, "password": "somepassword"}
        })

        mock_db_access = MagicMock()
        mock_db_access.get_user = lambda self, *args, **kwargs: None
        mock_db_access.get_failed_logins = lambda self, *args, **kwargs: None
        mock_db_access.update_failed_logins = lambda self, *args, **kwargs: 1
        server.db_access = mock_db_access

        self.app.post(AUTHENTICATE_ROUTE, data=body, headers=JSON_CONTENT_TYPE_HEADER)

        mock_audit.assert_called_once_with(
            'Invalid credentials used. username: {}, attempt: None.'.format(user_id)
        )

    @mock.patch('service.auditing.audit')
    def test_authenticate_user_audits_when_failed_login_exceeds_limit(self, mock_audit):
        user_id = 'userid'
        body = json.dumps({
            "credentials": {"user_id": user_id, "password": "somepassword"}
        })

        mock_db_access = MagicMock()
        mock_db_access.get_user = FakeUser(user_id, 'passwordhash', 20)
        mock_db_access.get_failed_logins = lambda self, *args, **kwargs: 20
        mock_db_access.update_failed_logins = lambda self, *args, **kwargs: 1
        server.db_access = mock_db_access

        self.app.post(AUTHENTICATE_ROUTE, data=body, headers=JSON_CONTENT_TYPE_HEADER)

        mock_audit.assert_called_once_with(
            'Too many bad logins. username: {}, attempt: 20.'.format(user_id)
        )

    @mock.patch('service.auditing.audit')
    @mock.patch('service.server.db_access.get_user',
                side_effect=Exception('Intentional test exception'))
    def test_authenticate_user_does_not_audit_when_error_occurs(self, mock_get_user, mock_audit):
        valid_body = json.dumps({
            "credentials": {"user_id": "userid1", "password": "somepassword"}
        })

        self.app.post(AUTHENTICATE_ROUTE, data=valid_body, headers=JSON_CONTENT_TYPE_HEADER)
        assert mock_audit.mock_calls == []

    @mock.patch('service.auditing.audit')
    def test_authenticate_does_not_audit_when_credentials_are_valid(self, mock_audit):
        valid_body = json.dumps({
            "credentials": {"user_id": "userid1", "password": "somepassword"}
        })

        mock_db_access = MagicMock()
        mock_db_access.get_user.return_value = FakeUser('userid1', 'passwordhash', 0)
        mock_db_access.get_failed_logins = lambda self, *args, **kwargs: 0
        mock_db_access.update_failed_logins = lambda self, *args, **kwargs: 1
        server.db_access = mock_db_access

        self.app.post(AUTHENTICATE_ROUTE, data=valid_body, headers=JSON_CONTENT_TYPE_HEADER)
        assert mock_audit.mock_calls == []

    @mock.patch('service.auditing.audit')
    def test_create_user_does_not_audit_when_invalid_request(self, mock_audit):
        self.app.post(
            CREATE_USER_ROUTE,
            data='{"invalid": "request"}',
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert mock_audit.mock_calls == []

    @mock.patch('service.auditing.audit')
    @mock.patch('service.server.db_access.create_user', return_value=False)
    def test_create_user_does_not_audit_when_user_already_exists(
            self, mock_create_user, mock_audit):

        valid_body = json.dumps({
            "user": {
                "user_id": "userid1", "password": "somepassword"
            }
        })

        self.app.post(CREATE_USER_ROUTE, data=valid_body, headers=JSON_CONTENT_TYPE_HEADER)
        assert mock_audit.mock_calls == []

    @mock.patch('service.auditing.audit')
    @mock.patch('service.server.db_access.create_user', return_value=True)
    def test_create_user_audits_when_creation_successful(self, mock_create_user, mock_audit):
        user_id = 'userid1'
        valid_body = json.dumps({
            "user": {
                "user_id": user_id,
                "password": "somepassword"
            }
        })

        self.app.post(CREATE_USER_ROUTE, data=valid_body, headers=JSON_CONTENT_TYPE_HEADER)
        mock_audit.assert_called_once_with('Created user {}'.format(user_id))

    @mock.patch('service.auditing.audit')
    @mock.patch('service.server.db_access.create_user', side_effect=Exception('Test exception'))
    def test_create_user_returns_500_response_when_an_error_occurs(
            self, mock_create_user, mock_audit):

        valid_body = json.dumps({
            "user": {"user_id": "userid", "password": "somepassword"}
        })

        self.app.post(CREATE_USER_ROUTE, data=valid_body, headers=JSON_CONTENT_TYPE_HEADER)
        assert mock_audit.mock_calls == []

    @mock.patch('service.auditing.audit')
    def test_update_user_does_not_audit_when_request_is_invalid(self, mock_audit):
        self.app.post(
            UPDATE_USER_ROUTE_FORMAT.format("userid"),
            data='{"invalid": "request"}',
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert mock_audit.mock_calls == []

    @mock.patch('service.auditing.audit')
    @mock.patch('service.server.db_access.update_user', return_value=0)
    def test_update_user_does_not_audit_when_user_not_found(self, mock_update_user, mock_audit):
        valid_body = '{"user": {"password": "somepassword"}}'

        self.app.post(
            UPDATE_USER_ROUTE_FORMAT.format('userid1'),
            data=valid_body,
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert mock_audit.mock_calls == []

    @mock.patch('service.auditing.audit')
    @mock.patch('service.server.db_access.update_user', return_value=1)
    def test_update_user_audits_when_user_update_successful(self, mock_update_user, mock_audit):
        user_id = 'userid1'
        valid_body = '{"user": {"password": "somepassword"}}'

        self.app.post(
            UPDATE_USER_ROUTE_FORMAT.format(user_id),
            data=valid_body,
            headers=JSON_CONTENT_TYPE_HEADER
        )

        mock_audit.assert_called_once_with('Updated user {}'.format(user_id))

    @mock.patch('service.auditing.audit')
    @mock.patch('service.server.db_access.update_user', side_effect=Exception('Test exception'))
    def test_update_user_does_not_audit_when_an_error_occurs(self, mock_update_user, mock_audit):
        valid_body = '{"user": {"password": "somepassword"}}'

        self.app.post(
            UPDATE_USER_ROUTE_FORMAT.format("userid1"),
            data=valid_body,
            headers=JSON_CONTENT_TYPE_HEADER
        )

        assert mock_audit.mock_calls == []

    @mock.patch('service.auditing.audit')
    @mock.patch('service.server.db_access.delete_user', return_value=0)
    def test_delete_user_does_not_audit_when_user_not_found(
            self, mock_delete_user, mock_audit):

        self.app.delete(DELETE_USER_ROUTE_FORMAT.format('userid1'))
        assert mock_audit.mock_calls == []

    @mock.patch('service.auditing.audit')
    @mock.patch('service.server.db_access.delete_user', return_value=1)
    def test_delete_user_audits_when_user_deletion_successful(self, mock_delete_user, mock_audit):
        user_id = 'userid1'
        self.app.delete(DELETE_USER_ROUTE_FORMAT.format(user_id))

        mock_audit.assert_called_once_with('Deleted user {}'.format(user_id))

    @mock.patch('service.auditing.audit')
    @mock.patch('service.server.db_access.delete_user', side_effect=Exception('Test exception'))
    def test_delete_user_does_not_audit_when_an_error_occurs(self, mock_delete_user, mock_audit):
        user_id = 'userid1'
        self.app.delete(DELETE_USER_ROUTE_FORMAT.format(user_id))
        assert mock_audit.mock_calls == []

    @mock.patch('service.auditing.audit')
    @mock.patch('service.server.db_access.update_failed_logins', return_value=0)
    def test_unlock_account_does_not_audit_when_user_not_found(self, mock_update, mock_audit):
        self.app.get(UNLOCK_ACCOUNT_ROUTE_FORMAT.format('userid'))
        assert mock_audit.mock_calls == []

    @mock.patch('service.auditing.audit')
    @mock.patch('service.server.db_access.update_failed_logins', return_value=1)
    def test_unlock_account_audits_when_failed_logins_reset(self, mock_update, mock_audit):
        user_id = 'userid1'

        self.app.get(UNLOCK_ACCOUNT_ROUTE_FORMAT.format(user_id))

        mock_audit.assert_called_once_with(
            'Reset failed login attempts for user {}'.format(user_id)
        )
