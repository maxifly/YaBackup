""" All integration constants """
import datetime

DOMAIN = 'yabackup'

CONF_PATH = 'path1'
CONF_CLIENT_ID = 'client_id'
CONF_CLIENT_SECRET = 'client_secret1'
CONF_ADD_TOKEN = 'add_token'
CONF_CHECK_CODE = 'check_code'
CONF_TOKEN = 'token'
CONF_REFRESH_TOKEN = 'refresh_token'
CONF_TOKEN_EXPIRES = 'token_expires_date'
CONF_MAX_REMOTE_FILE = 'max_remote_file'


DEFAULT_MAX_REMOTE_FILE = 10

REFRESH_TOKEN_DELTA = datetime.timedelta(days=30)


HEAD_CONTENT_TYPE = 'Content_Type'
HEAD_AUTHORIZATION = 'Authorization'
CONTENT_TYPE_FORM = 'application/x-www-form-urlencoded'

URL_GET_CODE = 'https://oauth.yandex.ru/authorize?response_type=code&client_id='
URL_GET_TOKEN = 'https://oauth.yandex.ru/token'

YANDEX_FIELD_ACCESS_TOKEN = 'access_token'
YANDEX_FIELD_REFRESH_TOKEN = 'refresh_token'

REST_TIMEOUT_SEC = 60
HTTP_OK = 200
