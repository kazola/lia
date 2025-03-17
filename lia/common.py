import os
import pathlib
import platform
import subprocess as sp
import sys
from lsb.connect import get_adapters
from rich.console import Console
from rich import print


console = Console()
PLATFORM = platform.system()
FILE_LOGGERS_TOML = (pathlib.Path.home() /
                     'Downloads' / 'lia' / 'loggers.toml')
FOL_APP_DATA = os.path.dirname(FILE_LOGGERS_TOML)
TIMEOUT_SCAN_MS = 10000
ad = get_adapters()[0]


def file_dl_path(name):
    return pathlib.Path.home() / 'Downloads' / 'lia' / name


def _scan(info, t_ms=TIMEOUT_SCAN_MS):
    assert type(info) is tuple
    t_s = int(t_ms / 1000)
    print('\n')
    s = f'Detecting {info} loggers nearby for {t_s} seconds...'
    with console.status(s, spinner='aesthetic', speed=.2, spinner_style="cyan"):
        ad.scan_for(t_ms)
    ls_pp = ad.scan_get_results()
    ls_pp = [p for p in ls_pp if p.identifier() in info]
    return ls_pp


def scan_for_tdo_loggers(t_ms=TIMEOUT_SCAN_MS):
    info = ('TDO', )
    return _scan(info, t_ms)


def scan_for_dox_loggers(t_ms=TIMEOUT_SCAN_MS):
    info = ('DO-1', 'DO-2')
    return _scan(info, t_ms)


def scan_for_all_loggers(t_ms=TIMEOUT_SCAN_MS):
    info = ('TDO', 'DO-1', 'DO-2')
    return _scan(info, t_ms)


def filter_by_loggers_file(ls_pp, d_lf):
    # get list of mac from loggers file
    ls_lf = list(d_lf.keys())
    ls_lf = [m.lower() for m in ls_lf]
    ls_pp = [p for p in ls_pp if p.address().lower() in ls_lf]
    return ls_pp


def clear_screen():
    if PLATFORM == 'Windows':
        os.system('cls')
        return
    os.system('clear')


def open_text_editor():
    s = 'notepad' if PLATFORM == 'Windows' else 'open'
    sp.run(f'{s} {FILE_LOGGERS_TOML}',
           shell=True, stdout=sp.PIPE, stderr=sp.PIPE)


def create_app_data_folder_and_file():
    if not os.path.exists(FOL_APP_DATA):
        os.system(f'mkdir {FOL_APP_DATA}')
    if not os.path.exists(FILE_LOGGERS_TOML):
        with open(FILE_LOGGERS_TOML, 'w') as f:
            f.write('[loggers]\n')
            f.write("# syntax MAC = SN\n")
            f.write('# "11:22:33:44:55:66" = "1234567"\n')


def get_sn_in_file_from_mac(d_file, mac):
    for mac_file, sn_file in d_file.items():
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


def check_sn_format(sn):
    return len(sn) == 7 and (
            sn.startswith('2') or sn.startswith('3'))


def print_menu_option(op, s):
    print(f"\t{op}[yellow4])[/yellow4] {s}")
