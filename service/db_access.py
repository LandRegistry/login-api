from sqlalchemy.exc import ProgrammingError, SQLAlchemyError  # type: ignore

from service import db

SQL_STATE_DUPLICATE_KEY = '23505'


class User(db.Model):  # type: ignore
    __tablename__ = 'users'

    user_id = db.Column(db.String(100), primary_key=True)
    password_hash = db.Column(db.String(64))
    failed_logins = db.Column(db.Integer)


def get_user(user_id, password_hash):
    return User.query.filter(
        User.user_id == user_id,
        User.password_hash == password_hash
    ).first()


def create_user(user_id, password_hash):
    try:
        user = User(user_id=user_id, password_hash=password_hash, failed_logins=0)  # type: ignore
        db.session.add(user)
        db.session.commit()
        return True
    except ProgrammingError as e:
        db.session.rollback()
        # This is what SQLAlchemy throws when a duplicate key error occurs
        if e.args and e.args[0].find(SQL_STATE_DUPLICATE_KEY) >= 0:
            return False
        else:
            raise Exception('An error occurred when trying to insert user into DB', e)


def update_user(user_id, password_hash):
    try:
        result = User.query.filter(User.user_id == user_id).update(
            values={'password_hash': password_hash}
        )
        db.session.commit()
        return result
    except SQLAlchemyError as e:
        db.session.rollback()
        raise e


def delete_user(user_id):
    try:
        result = User.query.filter(User.user_id == user_id).delete()
        db.session.commit()
        return result
    except SQLAlchemyError as e:
        db.session.rollback()
        raise e


def get_failed_logins(user_id):
    result = User.query.filter(User.user_id == user_id).first()
    if result:
        return result.failed_logins
    else:
        return None


def update_failed_logins(user_id, failed_logins):
    try:
        result = User.query.filter(User.user_id == user_id).update(
            values={'failed_logins': failed_logins}
        )
        db.session.commit()
        return result
    except SQLAlchemyError as e:
        db.session.rollback()
        raise e
