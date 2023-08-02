from flask import Blueprint, Flask
from flask_sqlalchemy import SQLAlchemy

__all__ = ["views", "errors", "models"]

gloss = Blueprint('gloss', __name__)
db = SQLAlchemy()

def create_app(environ):
    app = Flask(__name__)
    # SQLAlchemy no longer recognizes postgres:// URLs as "postgresql"
    # https://github.com/sqlalchemy/sqlalchemy/issues/6083
    database_url = environ["DATABASE_URL"]
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['DATABASE_URL'] = database_url
    app.config['SLACK_TOKEN'] = environ['SLACK_TOKEN']
    app.config['SLACK_WEBHOOK_URL'] = environ['SLACK_WEBHOOK_URL']

    db.init_app(app)

    from . import views, errors # noqa # pylint: disable=unused-import

    app.register_blueprint(gloss, url_prefix='/')

    return app
