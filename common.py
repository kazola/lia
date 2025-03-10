import os
import platform


PLATFORM = platform.system()


def clear_screen():
    if PLATFORM == 'Windows':
        os.system('cls')
        return
    os.system('clear')
