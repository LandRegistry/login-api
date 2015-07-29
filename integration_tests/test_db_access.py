import re
import pg8000
from config import CONFIG_DICT
from service import db_access

INSERT_USER_QUERY_FORMAT = (
    'insert into users(user_id, password_hash, failed_logins) values(%s, %s, %s)'
)

DELETE_ALL_USERS_QUERY = 'delete from users;'


def _get_db_connection_params():
    connection_string_regex = (
        r'^.*?//(?P<user>.+?):(?P<password>.+?)@(?P<host>.+?):(?P<port>\d+)/(?P<database>.+)$'
    )

    db_connection_string = CONFIG_DICT['SQLALCHEMY_DATABASE_URI']
    matches = re.match(connection_string_regex, db_connection_string)

    return {
        'user': matches.group('user'),
        'password': matches.group('password'),
        'host': matches.group('host'),
        'port': int(matches.group('port')),
        'database': matches.group('database'),
    }


DB_CONNECTION_PARAMS = _get_db_connection_params()


class TestDbAccess:

    def setup_method(self, method):
        self.connection = self._connect_to_db()
        self._delete_all_users()

    def teardown_method(self, method):
        self.connection.close()

    def test_get_user_returns_none_when_user_does_not_exist(self):
        user = db_access.get_user('nonexistinguser', 'passwordhash')
        assert user is None

    def test_get_user_returns_none_when_password_hash_does_not_match(self):
        user_id = 'userid1'
        self._create_user(user_id, 'passwordhash1', 0)
        user = db_access.get_user(user_id, 'passwordhash2')
        assert user is None

    def test_get_user_returns_none_when_password_hash_used_for_wrong_user(self):
        user_1_id = 'userid1'
        user_2_id = 'userid2'
        user_1_password_hash = 'passwordhash1'
        user_2_password_hash = 'passwordhash2'

        self._create_user(user_1_id, user_1_password_hash, 0)
        self._create_user(user_2_id, user_2_password_hash, 0)

        assert db_access.get_user(user_1_id, user_2_password_hash) is None
        assert db_access.get_user(user_2_id, user_1_password_hash) is None

    def test_get_user_returns_the_user_when_both_user_id_and_password_hash_match(self):
        user_id = 'userid1'
        password_hash = 'passwordhash1'
        failed_login_attempts = 1

        self._create_user(user_id, password_hash, failed_login_attempts)

        user = db_access.get_user(user_id, password_hash)

        assert user is not None
        assert user.user_id == user_id
        assert user.password_hash == password_hash
        assert user.failed_logins == failed_login_attempts

    def test_create_user_creates_new_user_when_id_not_used_yet(self):
        user_id = 'userid1'
        password_hash = 'passwordhash1'

        db_access.create_user(user_id, password_hash)
        user = db_access.get_user(user_id, password_hash)

        assert user is not None
        assert user.user_id == user_id
        assert user.password_hash == password_hash
        assert user.failed_logins == 0

    def test_create_user_returns_true_when_user_created(self):
        result = db_access.create_user('userid1', 'hash1')
        assert result is True

    def test_create_user_returns_false_when_duplicate(self):
        user_id = 'userid1'
        db_access.create_user(user_id, 'hash1')
        result = db_access.create_user(user_id, 'hash2')
        assert result is False

    def test_create_user_does_not_change_existing_user_when_duplicate(self):
        user_id = 'userid1'
        password_hash_1 = 'hash1'
        password_hash_2 = 'hash2'

        db_access.create_user(user_id, password_hash_1)
        db_access.create_user(user_id, password_hash_2)

        assert db_access.get_user(user_id, password_hash_1) is not None
        assert db_access.get_user(user_id, password_hash_2) is None

    def test_update_user_updates_user_when_one_exists(self):
        user_id = 'userid1'
        password_hash_1 = 'hash1'
        password_hash_2 = 'hash2'

        db_access.create_user(user_id, password_hash_1)
        db_access.update_user(user_id, password_hash_2)

        user = db_access.get_user(user_id, password_hash_2)
        assert user is not None

    def test_update_user_returns_one_when_user_updated_successfully(self):
        user_id = 'userid1'

        db_access.create_user(user_id, 'hash1')
        result = db_access.update_user(user_id, 'hash2')
        assert result == 1

    def test_update_user_returns_zero_when_user_does_not_exist(self):
        result = db_access.update_user('non-existing-user', 'hash1')
        assert result == 0

    def test_delete_user_deletes_user_when_one_exists(self):
        user_id = 'userid1'
        password_hash = 'hash1'

        db_access.create_user(user_id, password_hash)
        assert db_access.get_user(user_id, password_hash) is not None
        db_access.delete_user(user_id)
        assert db_access.get_user(user_id, password_hash) is None

    def test_delete_user_returns_one_when_user_deleted_successfully(self):
        user_id = 'userid1'
        password_hash = 'hash1'

        db_access.create_user(user_id, password_hash)
        result = db_access.delete_user(user_id)
        assert result == 1

    def test_delete_user_returns_zero_when_user_does_not_exist(self):
        result = db_access.delete_user('non-existing-user')
        assert result == 0

    def test_get_failed_logins_returns_the_right_number_for_existing_user(self):
        user_id = 'userid1'
        password_hash = 'hash1'
        failed_logins = 123

        self._create_user(user_id, password_hash, failed_logins)

        assert db_access.get_failed_logins(user_id) == failed_logins

    def test_get_failed_logins_returns_none_when_user_does_not_exist(self):
        assert db_access.get_failed_logins('non-existing-user-id') is None

    def test_update_failed_logins_updates_the_user_when_one_exists(self):
        user_id = 'userid1'
        failed_logins = 1234

        db_access.create_user(user_id, 'hash1')
        db_access.update_failed_logins(user_id, 1234)

        assert db_access.get_failed_logins(user_id) == failed_logins

    def test_update_failed_logins_returns_one_when_user_successfully_updated(self):
        user_id = 'userid1'
        db_access.create_user(user_id, 'hash1')
        result = db_access.update_failed_logins(user_id, 1234)
        assert result == 1

    def test_update_failed_logins_returns_zero_when_user_does_not_exist(self):
        result = db_access.update_failed_logins('non-existing-user-id', 1234)
        assert result == 0

    def _create_user(self, user_id, password_hash, failed_login_attempts):
        self.connection.cursor().execute(
            INSERT_USER_QUERY_FORMAT,
            (user_id, password_hash, failed_login_attempts)
        )

        return self.connection.commit()

    def _delete_all_users(self):
        self.connection.cursor().execute(DELETE_ALL_USERS_QUERY)
        self.connection.commit()

    def _connect_to_db(self):
        return pg8000.connect(**DB_CONNECTION_PARAMS)
