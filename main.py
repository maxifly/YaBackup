import base64

import yadisk
import requests

# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

TOKEN = 'y0_AgAAAABKKZKkAAjy3gAAAADX4p7jeWCmi6ScS7Sg4LRY864tReTAkiM'


def get_disk_info(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.

    y = yadisk.YaDisk(token=TOKEN)
    print(y.get_disk_info())

    # Выводит содержимое "/some/path"

    ll = list(y.listdir("/IT"))
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
    print_hi('2221705')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
