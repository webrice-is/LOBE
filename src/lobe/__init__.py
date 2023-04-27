"""Initialize Flask app."""
import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_executor import Executor
from flask_migrate import Migrate
from flask_security import Security, SQLAlchemyUserDatastore
from flask_sqlalchemy import SQLAlchemy

migrate = Migrate()
security = Security()
db = SQLAlchemy()
babel = Babel()
executor = Executor()


def add_app_config(app):
    """Add extra configuration to the LOBE app."""
    app.config["DATA_BASE_DIR"] = os.path.join(app.instance_path, "app_data/")
    app.config["TOKEN_DIR"] = os.path.join(app.config["DATA_BASE_DIR"], "tokens/")
    app.config["CUSTOM_TOKEN_DIR"] = os.path.join(app.config["DATA_BASE_DIR"], "custom_tokens/")
    app.config["RECORD_DIR"] = os.path.join(app.config["DATA_BASE_DIR"], "records/")
    app.config["CUSTOM_RECORDING_DIR"] = os.path.join(app.config["DATA_BASE_DIR"], "custom_recordings/")
    app.config["VIDEO_DIR"] = os.path.join(app.config["DATA_BASE_DIR"], "videos/")
    app.config["ZIP_DIR"] = os.path.join(app.config["DATA_BASE_DIR"], "zips/")
    app.config["TEMP_DIR"] = os.path.join(app.config["DATA_BASE_DIR"], "temp/")
    app.config["WAV_AUDIO_DIR"] = os.path.join(app.config["DATA_BASE_DIR"], "wav_audio/")
    app.config["WAV_CUSTOM_AUDIO_DIR"] = os.path.join(app.config["DATA_BASE_DIR"], "wav_custom_audio/")
    app.config["LOG_PATH"] = os.path.join(app.instance_path, "logs", "info.log")
    app.config["OTHER_DIR"] = os.path.join(app.instance_path, "other")
    app.config["STATIC_DATA_DIR"] = os.path.join(app.config["OTHER_DIR"], "static_data/")
    app.config["MANUAL_FNAME"] = "LOBE_manual.pdf"
    # create all the directories if they don't exist
    for dir_path in [
        app.config["TOKEN_DIR"],
        app.config["CUSTOM_TOKEN_DIR"],
        app.config["RECORD_DIR"],
        app.config["CUSTOM_RECORDING_DIR"],
        app.config["VIDEO_DIR"],
        app.config["ZIP_DIR"],
        app.config["TEMP_DIR"],
        app.config["WAV_AUDIO_DIR"],
        app.config["WAV_CUSTOM_AUDIO_DIR"],
        app.config["STATIC_DATA_DIR"],
    ]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)


def create_app():
    from lobe.filters import format_date
    from lobe.forms import ExtendedRegisterForm
    from lobe.models import Role, User
    from lobe.views.application import application
    from lobe.views.collection import collection
    from lobe.views.configuration import configuration
    from lobe.views.feed import feed
    from lobe.views.main import main
    from lobe.views.mos import mos
    from lobe.views.recording import recording
    from lobe.views.session import session
    from lobe.views.shop import shop
    from lobe.views.token import token
    from lobe.views.user import user
    from lobe.views.verification import verification

    # We need to set the instance path to the location of the config file
    app = Flask(__name__, instance_path=os.environ.get("FLASK_INSTANCE_PATH"), instance_relative_config=True)
    app.logger.setLevel(logging.DEBUG)

    app.config.from_pyfile("config.py")

    user_datastore = SQLAlchemyUserDatastore(db, User, Role)

    app.logger.addHandler(create_logger(app.config["LOG_PATH"]))

    db.init_app(app)
    migrate.init_app(app, db)
    # We attach our extended login and register form to the security extension
    # See: https://flask-security-too.readthedocs.io/en/stable/customizing.html#forms
    # It uses wtforms.
    security.init_app(app, user_datastore, register_form=ExtendedRegisterForm)
    babel.init_app(app)

    # register filters
    app.jinja_env.filters["datetime"] = format_date

    # Propagate background task exceptions
    app.config["EXECUTOR_TYPE"] = "process"
    # register blueprints
    app.register_blueprint(main)
    app.register_blueprint(collection)
    app.register_blueprint(verification)
    app.register_blueprint(token)
    app.register_blueprint(recording)
    app.register_blueprint(session)
    app.register_blueprint(user)
    app.register_blueprint(application)
    app.register_blueprint(configuration)
    app.register_blueprint(shop)
    app.register_blueprint(feed)
    app.register_blueprint(mos)

    executor.init_app(app)
    executor.add_default_done_callback(lambda future: print("background task done"))
    app.user_datastore = user_datastore

    # If we are behind a reverse proxy
    if app.config["BEHIND_REVERSE_PROXY"]:
        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    return app


def create_logger(log_path: str):
    logfile_mode = "w"
    if os.path.exists(log_path):
        logfile_mode = "a"
    else:
        os.makedirs(os.path.split(log_path)[0])
    handler = RotatingFileHandler(log_path, maxBytes=1000, backupCount=1, mode=logfile_mode)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s"))
    return handler
