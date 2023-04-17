import os

SECRET_KEY = "CHANGE_THIS"
SECURITY_PASSWORD_SALT = "SOME_SALT"

# postgresql://POSTGRES_USER:POSTGRES_PASSWORD@localhost:POSTGRES_PORT/POSTGRES_DB_NAME
SQLALCHEMY_DATABASE_URI = "postgresql://lobe:lobe@localhost:5432/lobe"

DEBUG = True
FLASK_DEBUG = True
APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))

# these should all have a trailing slash
DATA_BASE_DIR = os.path.join(APP_ROOT, os.pardir, "data/")
TOKEN_DIR = os.path.join(DATA_BASE_DIR, "tokens/")
CUSTOM_TOKEN_DIR = os.path.join(DATA_BASE_DIR, "custom_tokens/")
RECORD_DIR = os.path.join(DATA_BASE_DIR, "records/")
CUSTOM_RECORDING_DIR = os.path.join(DATA_BASE_DIR, "custom_recordings/")
VIDEO_DIR = os.path.join(DATA_BASE_DIR, "videos/")
ZIP_DIR = os.path.join(DATA_BASE_DIR, "zips/")
TEMP_DIR = os.path.join(DATA_BASE_DIR, "temp/")
WAV_AUDIO_DIR = os.path.join(DATA_BASE_DIR, "wav_audio/")
WAV_CUSTOM_AUDIO_DIR = os.path.join(DATA_BASE_DIR, "wav_custom_audio/")

# Path to the logging file
LOG_PATH = os.path.join(APP_ROOT, os.pardir, "logs", "info.log")

# For other static files, like the LOBE manual
OTHER_DIR = os.path.join(APP_ROOT, os.pardir, "other")
STATIC_DATA_DIR = os.path.join(OTHER_DIR, "static_data/")
MANUAL_FNAME = "LOBE_manual.pdf"

TOKEN_PAGINATION = 50
VERIFICATION_PAGINATION = 100
RECORDING_PAGINATION = 20
COLLECTION_PAGINATION = 20
USER_PAGINATION = 30
SESSION_PAGINATION = 50
CONF_PAGINATION = 30
MOS_PAGINATION = 20


SESSION_SZ = 50

RECAPTCHA_DATA_ATTRS = {"theme": "dark"}

SQLALCHEMY_TRACK_MODIFICATIONS = False

SECURITY_LOGIN_USER_TEMPLATE = "login_user.jinja"

# The default configuration id stored in database
DEFAULT_CONFIGURATION_ID = 1
