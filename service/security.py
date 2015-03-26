import hashlib
import binascii

HASH_ALGORITHM = 'sha256'
HASH_ITERATION_COUNT = 100000


def get_user_password_hash(user_id, password, salt):
    hash = hashlib.pbkdf2_hmac(
        HASH_ALGORITHM,
        (user_id + password).encode(),
        salt.encode(),
        HASH_ITERATION_COUNT
    )

    return binascii.hexlify(hash).decode()
