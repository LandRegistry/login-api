from collections import namedtuple
from mock import MagicMock
from service.db_access import DBAccess


class TestDBAccess:
    FakeUser = namedtuple("User", ['user_id', 'password_hash'])

    def setup_method(self, method):
        pass

    def test_get_user_uses_sqlalchemy_to_retrieve_user_from_db(self):
        db_access = DBAccess(MagicMock())

        user_id = 'userid123'
        password_hash = 'passwordhash123'

        mock_user_class = MagicMock()
        mock_user_class.query.filter.return_value.first.return_value = self.FakeUser(user_id, password_hash)
        db_access.User = mock_user_class

        db_access.get_user(user_id, password_hash)

        mock_user_class.query.filter.assert_called_once_with(
            mock_user_class.User.user_id == user_id,
            mock_user_class.User.password_hash == password_hash
        )

        mock_user_class.query.filter.return_value.first.assert_called_once_with()

    def test_get_user_returns_result_from_sqlalchemy(self):
        db_access = DBAccess(MagicMock())
        mock_user_class = MagicMock()

        user_id = 'userid123'
        password_hash = 'passwordhash123'

        mock_user_class.query.filter.return_value.first.return_value = self.FakeUser(user_id, password_hash)

        db_access.User = mock_user_class

        result = db_access.get_user(user_id, password_hash)

        assert result.user_id == user_id
        assert result.password_hash == password_hash

    def test_create_user_uses_sqlalchemy_for_db_insert(self):
        class FakeUserModel():
            def __init__(self, user_id, password_hash):
                self.user_id = user_id
                self.password_hash = password_hash
                
            def __eq__(self, other):
                return self.user_id == other.user_id and self.password_hash == other.password_hash
        
        mock_sqlalchemy = MagicMock()
        mock_sqlalchemy.Model = FakeUserModel
        db_access = DBAccess(mock_sqlalchemy)

        user_id = 'userid123'
        password_hash = 'passwordhash123'

        result = db_access.create_user(user_id, password_hash)
        
        assert result == True
        mock_sqlalchemy.session.add.assert_called_once_with(FakeUserModel(user_id, password_hash))
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

        mock_user_class.query.filter.assert_called_once_with(mock_user_class.User.user_id == user_id)
        mock_user_class.query.filter.return_value.update.assert_called_once_with(values={'password_hash': password_hash})
        mock_sqlalchemy.session.commit.assert_called_once_with()

    def test_update_user_returns_sqlalchemy_update_result(self):
        db_access = DBAccess(MagicMock())
        expected_result = 123

        mock_user_class = MagicMock()
        mock_user_class.query.filter.return_value.update.return_value = expected_result
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

        mock_user_class.query.filter.assert_called_once_with(mock_user_class.User.user_id == user_id)
        mock_user_class.query.filter.return_value.delete.assert_called_once_with()
        mock_sqlalchemy.session.commit.assert_called_once_with()

    def test_delete_user_returns_sqlalchemy_deletion_result(self):
        db_access = DBAccess(MagicMock())
        expected_result = 123

        mock_user_class = MagicMock()
        mock_user_class.query.filter.return_value.delete.return_value = expected_result
        db_access.User = mock_user_class

        result = db_access.delete_user('userid123')
        assert result == expected_result
