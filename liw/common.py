import os
import pathlib
import platform
import subprocess as sp
import sys

from lsb.connect import get_adapters


PLATFORM = platform.system()
FILE_LOGGERS_TOML = (pathlib.Path.home() /
                     'Downloads' / 'liw' / 'loggers.toml')
FOL_APP_DATA = os.path.dirname(FILE_LOGGERS_TOML)
TIMEOUT_SCAN_MS = 10000
ad = get_adapters()[0]


def scan_for_tdo_loggers(t_ms=TIMEOUT_SCAN_MS):
    info = 'TDO'
    assert len(info) == 3
    t_s = int(t_ms / 1000)
    print(f'\nSearching {info} loggers during {t_s} seconds, please wait...')
    ad.scan_for(t_ms)
    ls_pp = ad.scan_get_results()
    ls_pp = [p for p in ls_pp if p.identifier() == info]
    return ls_pp


def scan_for_dox_loggers(t_ms=TIMEOUT_SCAN_MS):
    t_s = int(t_ms / 1000)
    print(f'\nSearching Dissolved Oxygen loggers during {t_s} seconds, please wait...')
    ad.scan_for(t_ms)
    ls_pp = ad.scan_get_results()
    ls_pp = [p for p in ls_pp if p.identifier() in ('DO-1', 'DO-2')]
    return ls_pp


def clear_screen():
    if PLATFORM == 'Windows':
        os.system('cls')
        return
    os.system('clear')


def open_text_editor():
    if PLATFORM == 'Windows':
        sp.run(f'notepad {FILE_LOGGERS_TOML}',
               shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    else:
        sp.run(f'open {FILE_LOGGERS_TOML}',
               shell=True, stdout=sp.PIPE, stderr=sp.PIPE)


def create_app_data_folder_and_file():
    if not os.path.exists(FOL_APP_DATA):
        os.system(f'mkdir {FOL_APP_DATA}')
    if not os.path.exists(FILE_LOGGERS_TOML):
        with open(FILE_LOGGERS_TOML, 'w') as f:
            f.write('[loggers]\n')
            f.write("# syntax\n")
            f.write('# "1234567" = "11:22:33:44:55:66"\n')


def get_sn_in_file_from_mac(d_file, mac):
    for sn_file, mac_file in d_file.items():
        if mac.lower() == mac_file.lower():
            return sn_file
    return mac


def get_remote_loggers_file():
    token = sys.argv[1]
    if len(token) != 4:
        print('error: token too short')
        sys.exit(1)

    # use token to replace any local loggers file
    if os.path.exists(FILE_LOGGERS_TOML):
        print(f'deleting previous file {FILE_LOGGERS_TOML}')
        os.unlink(FILE_LOGGERS_TOML)
    print('trying to download updated loggers file')


