#!/usr/bin/env python3

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from service import app, db

# db.create_all() needs all models to be imported explicitly (not *)
from service.db_access import User


migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
