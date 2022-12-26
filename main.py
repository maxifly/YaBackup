import yadisk

# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

TOKEN = 'y0_AgAAAABKKZKkAAjy3gAAAADX4p7jeWCmi6ScS7Sg4LRY864tReTAkiM'


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.

    y = yadisk.YaDisk(token=TOKEN)
    print(y.get_disk_info())

    # Выводит содержимое "/some/path"

    ll = list(y.listdir("/IT"))
    print(ll)



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
