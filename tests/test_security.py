import pytest
from service import security


class TestSecurity:

    def test_get_user_password_hash_returns_same_hash_for_same_data(self):
        hash1 = security.get_user_password_hash('user1', 'password1', 'salt1')
        hash2 = security.get_user_password_hash('user1', 'password1', 'salt1')
        assert hash1 == hash2

    def test_get_userpass_hash_returns_different_hash_for_diff_salts(self):
        hash1 = security.get_user_password_hash('user1', 'password1', 'salt1')
        hash2 = security.get_user_password_hash('user1', 'password1', 'salt2')
        assert hash1 != hash2

    def test_get_userpass_hash_returns_different_hash_for_diff_users(self):
        hash1 = security.get_user_password_hash('user1', 'password1', 'salt1')
        hash2 = security.get_user_password_hash('user2', 'password1', 'salt1')
        assert hash1 != hash2

    def test_get_userpass_returns_different_hash_for_different_passwords(self):
        hash1 = security.get_user_password_hash('user1', 'password1', 'salt1')
        hash2 = security.get_user_password_hash('user1', 'password2', 'salt1')
        assert hash1 != hash2
