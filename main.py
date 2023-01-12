import base64
import datetime

import yadisk
import requests

# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

TOKEN = 'y0_AgAAAABKKZKkAAjy3gAAAADX4p7jeWCmi6ScS7Sg4LRY864tReTAkiM'


def upload_file():
    print('Start')  # Press Ctrl+F8 to toggle the breakpoint.

    y = yadisk.YaDisk(token=TOKEN)
    print(y.get_disk_info())
    print(datetime.datetime.now())
    y.upload('/home/maxim/.homeassistant/backups/cb7d9207.tar', '/ha_test/Core 2023.1.0.dev17.tar', overwrite=True,
             n_retries=3, retry_interval=5.0, timeout=(15.0, 250.0))
    print(datetime.datetime.now())
    ll = list(y.listdir("/ha_test"))
    print(ll)

HEAD_CONTENT_TYPE = 'Content_Type'
HEAD_AUTHORIZATION = 'Authorization'
CONTENT_TYPE_FORM = 'application/x-www-form-urlencoded'
url = 'https://oauth.yandex.ru/token'

def print_hi(check_code):

    headers = {}
    headers[HEAD_CONTENT_TYPE] = CONTENT_TYPE_FORM
    headers[HEAD_AUTHORIZATION] = 'Basic ' + str(get_auth_string('38ded937723b40719431aba205a53ac1', 'd60561312c8c452a89cb5cce068b42fe'))
    responce = requests.post(url, headers=headers, data='grant_type=authorization_code&code='+ check_code)
    json_result = responce.json()
    i = 1

def get_auth_string(client_id, client_secret):
    return base64.b64encode(bytes(client_id + ':' + client_secret, 'utf-8')).decode('utf-8')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    upload_file()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
