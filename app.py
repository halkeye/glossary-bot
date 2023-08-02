from os import environ
from gloss import create_app, db
from flask_migrate import Migrate

app = create_app(environ)

migrate = Migrate(app, db)
