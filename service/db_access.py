from sqlalchemy.exc import ProgrammingError
SQL_STATE_DUPLICATE_KEY = '23505'


class DBAccess():

    def __init__(self, db):
        self.db = db

        class User(db.Model):
            __tablename__ = 'users'

            user_id = db.Column(db.String(100), primary_key=True)
            password_hash = db.Column(db.String(64))
            failed_logins = db.Column(db.Integer)

        self.User = User

    def get_user(self, user_id, password_hash):
        return self.User.query.filter(
            self.User.user_id == user_id,
            self.User.password_hash == password_hash
        ).first()

    def create_user(self, user_id, password_hash):
        try:
            user = self.User(
                user_id=user_id,
                password_hash=password_hash,
                failed_logins=0
            )
            self.db.session.add(user)
            self.db.session.commit()
            return True
        except ProgrammingError as e:
            # This is what SQLAlchemy throws when a duplicate key error occurs
            if e.args and e.args[0].find(SQL_STATE_DUPLICATE_KEY) >= 0:
                return False
            else:
                raise Exception('An error occurred when trying '
                                'to insert user into DB', e)

    def update_user(self, user_id, password_hash):
        result = self.User.query.filter(self.User.user_id == user_id).update(
            values={'password_hash': password_hash}
        )
        self.db.session.commit()
        return result

    def delete_user(self, user_id):
        result = self.User.query.filter(self.User.user_id == user_id).delete()
        self.db.session.commit()
        return result

    def get_failed_logins(self, user_id):
        result = self.User.query.filter(self.User.user_id == user_id).first()
        if result:
            return result.failed_logins
        else:
            return None

    def update_failed_logins(self, user_id, failed_logins):
        result = self.User.query.filter(self.User.user_id == user_id).update(
            values={'failed_logins': failed_logins}
        )
        self.db.session.commit()
        return result
