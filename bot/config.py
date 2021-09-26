import os

from dotenv import load_dotenv

load_dotenv()

MAX_VARCHAR_LENGTH = 255

BOT_TOKEN = os.environ.get('BOT_TOKEN', 'DO_NOT_PASTE_TOKEN_HERE')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.environ.get('RABBITMQ_PORT', '5672'))
RABBITMQ_QUEUE_NAMES = {
    'bot2backend': 'support_backend',
    'backend2bot': 'support_bot'
}

MYSQL_HOST = os.environ.get('MYSQL_HOST', '127.0.0.1')
MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
MYSQL_DBNAME = os.environ.get('MYSQL_DBNAME', 'dbname')
MYSQL_USER = os.environ.get('MYSQL_USER', 'username')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'password')
MYSQL_PREFIX = os.environ.get('MYSQL_PREFIX', 'support_')

# TODO check level of base_dir
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOT_STATIC_DIR = os.path.join(BASE_DIR, 'static')
DEFAULT_AVATAR_PATH = os.path.join(BOT_STATIC_DIR, 'user-profile.png')
WWW_DIR = os.path.join('/var/www/supportbot/')
STATIC_DIR = os.path.join(WWW_DIR, 'static/')
UPLOAD_DIR = os.path.join(STATIC_DIR, 'files/')
TELEGRAM_API_FILE_DOWNLOAD_LIMIT = 20 * (1024 ** 2)

CONTENT_TYPES = ['audio', 'photo', 'voice', 'video', 'document', 'text', 'location', 'venue', 'contact', 'sticker']
SUPPORTED_ATTACHMENTS_TYPES = ['photo', 'video', 'document', 'location', 'venue', 'contact']
DOWNLOADABLE_ATTACHMENTS_TYPES = ['photo', 'video', 'document']
