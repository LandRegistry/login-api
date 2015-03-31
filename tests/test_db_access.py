from collections import namedtuple
from mock import MagicMock
from service.db_access import DBAccess


class TestDBAccess:
    FakeUser = namedtuple(
        "User",
        ['user_id', 'password_hash', 'failed_logins']
    )

    def setup_method(self, method):
        pass

    def test_get_user_uses_sqlalchemy_to_retrieve_user_from_db(self):
        db_access = DBAccess(MagicMock())

        user_id = 'userid123'
        password_hash = 'passwordhash123'
        failed_logins = 0

        mock_user_class = MagicMock()
        first_return_val = mock_user_class.query.filter.return_value.first
        first_return_val.return_value = self.FakeUser(
            user_id,
            password_hash,
            failed_logins
        )
        db_access.User = mock_user_class

        db_access.get_user(user_id, password_hash)

        mock_user_class.query.filter.assert_called_once_with(
            mock_user_class.User.user_id == user_id,
            mock_user_class.User.password_hash == password_hash
        )

        first_return_val = mock_user_class.query.filter.return_value.first
        first_return_val.assert_called_once_with()

    def test_get_user_returns_result_from_sqlalchemy(self):
        db_access = DBAccess(MagicMock())
        mock_user_class = MagicMock()

        user_id = 'userid123'
        password_hash = 'passwordhash123'
        failed_logins = 0

        first_return_value = mock_user_class.query.filter.return_value.first
        first_return_value.return_value = self.FakeUser(
            user_id,
            password_hash,
            failed_logins
        )

        db_access.User = mock_user_class

        result = db_access.get_user(user_id, password_hash)

        assert result.user_id == user_id
        assert result.password_hash == password_hash

    def test_create_user_uses_sqlalchemy_for_db_insert(self):
        class FakeUserModel():
            def __init__(self, user_id, password_hash, failed_logins):
                self.user_id = user_id
                self.password_hash = password_hash
                self.failed_logins = failed_logins

            def __eq__(self, other):
                return (
                    self.user_id == other.user_id and
                    self.password_hash == other.password_hash
                )

        mock_sqlalchemy = MagicMock()
        mock_sqlalchemy.Model = FakeUserModel
        db_access = DBAccess(mock_sqlalchemy)

        user_id = 'userid123'
        password_hash = 'passwordhash123'

        result = db_access.create_user(user_id, password_hash)

        assert result
        mock_sqlalchemy.session.add.assert_called_once_with(
            FakeUserModel(user_id, password_hash, 0)
        )
        mock_sqlalchemy.session.commit.assert_called_once_with()

    def test_update_user_uses_sqlalchemy_for_db_update(self):
        mock_sqlalchemy = MagicMock()
        db_access = DBAccess(mock_sqlalchemy)

        user_id = 'userid123'
        password_hash = 'passwordhash123'

        mock_user_class = MagicMock()
        mock_user_class.query.filter.return_value.update.return_value = 1
        db_access.User = mock_user_class

        db_access.update_user(user_id, password_hash)

        mock_user_class.query.filter.assert_called_once_with(
            mock_user_class.User.user_id == user_id
        )
        mock_return_update = mock_user_class.query.filter.return_value.update
        mock_return_update.assert_called_once_with(
            values={'password_hash': password_hash}
        )
        mock_sqlalchemy.session.commit.assert_called_once_with()

    def test_update_user_returns_sqlalchemy_update_result(self):
        db_access = DBAccess(MagicMock())
        expected_result = 123

        mock_user_class = MagicMock()
        mock_return_val = mock_user_class.query.filter.return_value
        mock_return_val.update.return_value = expected_result
        db_access.User = mock_user_class

        result = db_access.update_user('userid123', 'passwordhash123')

        assert result == expected_result

    def test_delete_user_uses_sqlalchemy_for_db_delete(self):
        mock_sqlalchemy = MagicMock()
        db_access = DBAccess(mock_sqlalchemy)

        user_id = 'userid123'

        mock_user_class = MagicMock()
        mock_user_class.query.filter.return_value.update.return_value = 1
        db_access.User = mock_user_class

        db_access.delete_user(user_id)

        mock_user_class.query.filter.assert_called_once_with(
            mock_user_class.User.user_id == user_id
        )
        mock_filter_return_val = mock_user_class.query.filter.return_value
        mock_filter_return_val.delete.assert_called_once_with()
        mock_sqlalchemy.session.commit.assert_called_once_with()

    def test_delete_user_returns_sqlalchemy_deletion_result(self):
        db_access = DBAccess(MagicMock())
        expected_return = 123

        mock_user_class = MagicMock()
        mock_class_return_value = mock_user_class.query.filter.return_value
        mock_class_return_value.delete.return_value = expected_return
        db_access.User = mock_user_class

        result = db_access.delete_user('userid123')
        assert result == expected_return

    def test_get_failed_logins_returns_result_for_existing_user(self):
        db_access = DBAccess(MagicMock())
        mock_user_class = MagicMock()

        user_id = 'userid123'
        password_hash = 'passwordhash123'
        failed_logins = 1

        first_return_val = mock_user_class.query.filter.return_value
        first_return_val.first.return_value = self.FakeUser(
            user_id,
            password_hash,
            failed_logins
        )

        db_access.User = mock_user_class

        result = db_access.get_failed_logins(user_id)

        assert result == failed_logins

    def test_get_failed_logins_returns_result_for_non_existant_user(self):
        db_access = DBAccess(MagicMock())
        mock_user_class = MagicMock()

        user_id = 'userid123'

        first_return_val = mock_user_class.query.filter.return_value
        first_return_val.first.return_value = None

        db_access.User = mock_user_class

        result = db_access.get_failed_logins(user_id)

        assert result is None

    def test_update_failed_logins_returns_result_for_existing_user(self):
        db_access = DBAccess(MagicMock())
        mock_user_class = MagicMock()

        user_id = 'userid123'
        expected_result = 1

        first_return_val = mock_user_class.query.filter.return_value
        first_return_val.update.return_value = 1

        db_access.User = mock_user_class

        num_of_rows = db_access.update_failed_logins(user_id, 0)

        assert num_of_rows == expected_result

    def test_update_failed_logins_uses_sqlalchemy_for_db_update(self):
        mock_sqlalchemy = MagicMock()
        db_access = DBAccess(mock_sqlalchemy)

        user_id = 'userid123'
        failed_logins = 0

        mock_user_class = MagicMock()
        first_return_val = mock_user_class.query.filter.return_value
        first_return_val.update.return_value = 1
        db_access.User = mock_user_class

        db_access.update_failed_logins(user_id, failed_logins)

        mock_user_class.query.filter.assert_called_once_with(
            mock_user_class.User.user_id == user_id
        )
        first_return_val.update.assert_called_once_with(
            values={'failed_logins': failed_logins}
        )
        mock_sqlalchemy.session.commit.assert_called_once_with()

    def test_update_failed_logins_returns_sqlalchemy_update_result(self):
        db_access = DBAccess(MagicMock())

        user_id = 'userid123'
        failed_logins = 0

        mock_user_class = MagicMock()
        first_return_val = mock_user_class.query.filter.return_value
        first_return_val.update.return_value = 1
        db_access.User = mock_user_class

        result = db_access.update_failed_logins(user_id, failed_logins)

        assert result == 1
