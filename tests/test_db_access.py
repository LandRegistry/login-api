from collections import namedtuple
import mock
from service.db_access import (create_user, delete_user, get_failed_logins, get_user,
                               update_failed_logins, update_user)


FakeUser = namedtuple('User', ['user_id', 'password_hash', 'failed_logins'])


@mock.patch('service.db_access.User')
def test_get_user_uses_sqlalchemy_to_retrieve_user_from_db(mock_user_class):
    user_id = 'userid123'
    password_hash = 'passwordhash123'
    failed_logins = 0

    first_return_val = mock_user_class.query.filter.return_value.first
    first_return_val.return_value = FakeUser(user_id, password_hash, failed_logins)

    get_user(user_id, password_hash)

    mock_user_class.query.filter.assert_called_once_with(
        mock_user_class.User.user_id == user_id,
        mock_user_class.User.password_hash == password_hash
    )

    first_return_val = mock_user_class.query.filter.return_value.first
    first_return_val.assert_called_once_with()


@mock.patch('service.db_access.User')
def test_get_user_returns_result_from_sqlalchemy(mock_user_class):
    user_id = 'userid123'
    password_hash = 'passwordhash123'
    failed_logins = 0

    first_return_value = mock_user_class.query.filter.return_value.first
    first_return_value.return_value = FakeUser(user_id, password_hash, failed_logins)

    result = get_user(user_id, password_hash)

    assert result.user_id == user_id
    assert result.password_hash == password_hash


@mock.patch('service.db.session.add')
@mock.patch('service.db.session.commit')
def test_create_user_uses_sqlalchemy_for_db_insert(mock_session_commit,
                                                   mock_session_add):
    user_id = 'userid123'
    password_hash = 'passwordhash123'
    fake_user = FakeUser(user_id, password_hash, 0)

    with mock.patch('service.db_access.User', return_value=fake_user):
        result = create_user(user_id, password_hash)

    assert result

    mock_session_add.assert_called_once_with(FakeUser(user_id, password_hash, 0))
    mock_session_commit.assert_called_once_with()


@mock.patch('service.db.session.commit')
@mock.patch('service.db_access.User.query.filter')
@mock.patch('service.db_access.User')
def test_update_user_uses_sqlalchemy_for_db_update(mock_user_class, mock_filter,
                                                   mock_session_commit):
    user_id = 'userid123'
    password_hash = 'passwordhash123'

    update_user(user_id, password_hash)

    mock_filter.assert_called_once_with(
        mock_user_class.User.user_id == user_id
    )
    mock_return_update = mock_filter.return_value.update
    mock_return_update.assert_called_once_with(
        values={'password_hash': password_hash}
    )
    mock_session_commit.assert_called_once_with()


@mock.patch('service.db_access.User')
def test_update_user_returns_sqlalchemy_update_result(mock_user_class):
    expected_result = 123

    mock_return_val = mock_user_class.query.filter.return_value
    mock_return_val.update.return_value = expected_result

    result = update_user('userid123', 'passwordhash123')

    assert result == expected_result


@mock.patch('service.db.session.commit')
@mock.patch('service.db_access.User.query.filter')
@mock.patch('service.db_access.User')
def test_delete_user_uses_sqlalchemy_for_db_delete(mock_user_class, mock_filter,
                                                   mock_session_commit):
    user_id = 'userid123'

    delete_user(user_id)

    mock_filter.assert_called_once_with(
        mock_user_class.User.user_id == user_id
    )
    mock_filter_return_val = mock_user_class.query.filter.return_value
    mock_filter_return_val.delete.assert_called_once_with()
    mock_session_commit.assert_called_once_with()


@mock.patch('service.db_access.User')
def test_delete_user_returns_sqlalchemy_deletion_result(mock_user_class):
    expected_return = 123

    mock_class_return_value = mock_user_class.query.filter.return_value
    mock_class_return_value.delete.return_value = expected_return

    result = delete_user('userid123')
    assert result == expected_return


@mock.patch('service.db_access.User')
def test_get_failed_logins_returns_result_for_existing_user(mock_user_class):
    user_id = 'userid123'
    password_hash = 'passwordhash123'
    failed_logins = 1

    first_return_val = mock_user_class.query.filter.return_value
    first_return_val.first.return_value = FakeUser(
        user_id,
        password_hash,
        failed_logins
    )

    result = get_failed_logins(user_id)

    assert result == failed_logins


@mock.patch('service.db_access.User')
def test_get_failed_logins_returns_result_for_non_existant_user(mock_user_class):
    user_id = 'userid123'

    first_return_val = mock_user_class.query.filter.return_value
    first_return_val.first.return_value = None

    result = get_failed_logins(user_id)

    assert result is None


@mock.patch('service.db_access.User')
def test_update_failed_logins_returns_result_for_existing_user(mock_user_class):
    user_id = 'userid123'
    expected_result = 1

    first_return_val = mock_user_class.query.filter.return_value
    first_return_val.update.return_value = 1

    num_of_rows = update_failed_logins(user_id, 0)

    assert num_of_rows == expected_result


@mock.patch('service.db.session.commit')
@mock.patch('service.db_access.User.query.filter')
@mock.patch('service.db_access.User')
def test_update_failed_logins_uses_sqlalchemy_for_db_update(mock_user_class, mock_filter,
                                                            mock_session_commit):
    user_id = 'userid123'
    failed_logins = 0

    update_failed_logins(user_id, failed_logins)

    mock_filter.assert_called_once_with(
        mock_user_class.User.user_id == user_id
    )
    mock_return_update = mock_filter.return_value.update
    mock_return_update.assert_called_once_with(
        values={'failed_logins': failed_logins}
    )
    mock_session_commit.assert_called_once_with()


@mock.patch('service.db_access.User')
def test_update_failed_logins_returns_sqlalchemy_update_result(mock_user_class):
    user_id = 'userid123'
    failed_logins = 0

    first_return_val = mock_user_class.query.filter.return_value
    first_return_val.update.return_value = 1

    result = update_failed_logins(user_id, failed_logins)

    assert result == 1
