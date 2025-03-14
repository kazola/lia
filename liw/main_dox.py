import os.path
import sys
import time
from lsb.cmd import (
    get_rx,
    cmd_gfv,
    cmd_sws,
    cmd_sts,
    cmd_gtm,
    cmd_stm,
    cmd_frm,
    cmd_wli,
    cmd_bat,
    cb_rx_noti,
    cmd_gdo,
    cmd_cfg
)
from lsb.connect import (
    connect_mac,
    my_disconnect
)
from lsb.li import (
    UUID_S,
    UUID_T
)
import toml
from liw.common import (
    clear_screen,
    create_app_data_folder_and_file,
    FILE_LOGGERS_TOML,
    open_text_editor,
    scan_for_dox_loggers,
    get_sn_in_file_from_mac,
    get_remote_loggers_file
)


BAT_FACTOR_DOX = 0.4545
g_app_cfg = {
    'rerun': False,
    'DRI': 900,
    'DFN': 'LAB'
}


def _e(e):
    if get_rx():
        return
    raise Exception(f'error DOX: {e}')


def _p(s, t=0):
    print(('\t' * t) + s)


def _pt(s):
    return _p(s, t=1)


def _deploy_one_dox_logger(p, sn):

    mac = p.address()

    if not sn.startswith('2') or sn.startswith('3'):
        _p(f'error: {mac} has bad SN {sn}')
        input()

    _p(f'\ndeploying DOX logger {sn} mac {mac}')

    if not connect_mac(p, mac):
        _e('connecting')
    p.notify(UUID_S, UUID_T, cb_rx_noti)

    # start sending commands
    ver = cmd_gfv(p)
    _e('command version')
    ver = ver[6:].decode()
    _pt(f'version {ver}')

    g = ("-3.333333", "-4.444444", None, None)
    cmd_sws(p, g)
    _e('command stop with string')
    _pt('stop OK')

    v = cmd_sts(p)
    _e('command status')
    _pt(f'status {v}')

    v = cmd_gtm(p)
    _e('command get_time')
    _pt(f'get time {v}')

    cmd_stm(p)
    _e('command set time')
    _pt(f'set time OK')

    cmd_frm(p)
    _e('command format')
    _pt('format OK')

    cmd_wli(p, sn)
    _e('command wli_sn')
    time.sleep(.1)

    v = cmd_bat(p)
    _e('command bat')
    v /= BAT_FACTOR_DOX
    _pt(f'bat = {int(v)} mV')

    rv = cmd_gdo(p)
    _e('command GDO')
    _pt(f'gdo = {rv}')

    # send CFG command
    d_cfg = {
        "DFN": g_app_cfg['DFN'],
        "TMP": 0,
        "PRS": 0,
        "DOS": 1,
        "DOP": 1,
        "DOT": 1,
        "TRI": 10,
        "ORI": 10,
        "DRI": g_app_cfg['DRI'],
        "PRR": 1,
        "PRN": 1,
        "STM": "2012-11-12 12:14:00",
        "ETM": "2040-11-12 12:14:20",
        "LED": 1
    }
    cmd_cfg(p, d_cfg)
    _e('command CFG')
    _pt('configuration CFG sent OK')


    my_disconnect(p)
    _pt('disconnected')


def menu():
    create_app_data_folder_and_file()
    ls_pp = []
    c = ''

    while 1:

        clear_screen()

        # we not always do a scan
        skip_scan = c in ('r', 'e', 'd', 'i')
        if not skip_scan:
            ls_pp = scan_for_dox_loggers()

        # read loggers file
        dlf = {}
        if os.path.exists(FILE_LOGGERS_TOML):
            dlf = toml.load(FILE_LOGGERS_TOML)['loggers']

        # build menu
        bn = os.path.basename(FILE_LOGGERS_TOML)
        if len(dlf) == 0:
            _p(f'warning: you have 0 files on your file {bn}')
        m = {
            's': f'scan again',
            'r': f'set run flag, now is {g_app_cfg["rerun"]}',
            'e': f'edit file {bn}, now it has {len(dlf)} loggers',
            'd': f'set deployment name, now {g_app_cfg["DFN"]}',
            'i': f'set DO interval, now {g_app_cfg["DRI"]}',
            'q': 'quit'
        }

        # display menu options for user to choose from
        _p('\nSelect an option...')
        for k, v in m.items():
            if not k.isnumeric():
                _p(f'\t{k}) {v}')

        # display list of deployable DOX loggers
        ls_file_macs = [m.lower() for m in dlf.values()]
        ls_pp = [p for p in ls_pp if p.address().lower() in ls_file_macs ]
        if ls_pp:
            _p('\n... or deploy one of the Dissolved Oxygen loggers detected nearby:')
            for i, per in enumerate(ls_pp):
                sn = get_sn_in_file_from_mac(dlf, per.address())
                _p(f'\t{i}) deploy {sn}')
                # add to menu dictionary
                m[str(i)] = per.address()

        # grab user choice
        c = input('\n-> ')
        if c not in m.keys():
            continue
        if c == 'q':
            break
        if c == 'r':
            g_app_cfg['rerun'] = not g_app_cfg['rerun']
            continue
        if c == 's':
            # just go at it again
            continue
        if c == "d":
            i = str(input("\t\t enter new deployment name -> "))
            if len(i) != 3:
                print("invalid input: must be 3 letters long")
                time.sleep(1)
                continue
            g_app_cfg['DFN'] = i
            continue
        if c == "i":
            try:
                i = int(input("\t\t enter new interval -> "))
            except ValueError:
                print("invalid input: must be number")
                time.sleep(1)
                continue
            valid = (30, 60, 300, 600, 900, 3600, 7200)
            if i not in valid:
                print("invalid interval: must be {}".format(valid))
                time.sleep(1)
                continue
            g_app_cfg['DRI'] = i
            continue
        if c == 'e':
            open_text_editor()
            continue
        if not c.isnumeric():
            continue

        # deploy logger
        my_p = ls_pp[int(c)]
        try:
            sn = get_sn_in_file_from_mac(dlf, my_p.address())
            _deploy_one_dox_logger(my_p, sn)
            _p(f'\ndeployment of DOX logger {sn} went OK!')
        except (Exception,) as ex:
            _p(f'\nerror: {ex}')

        try:
            my_disconnect(my_p)
        except (Exception,) as ex:
            _p(f'\nerror disconnecting: {ex}')

        _p('\npress ENTER to go back to menu')
        input()


def main():
    if len(sys.argv) == 2:
        # online mode
        get_remote_loggers_file()
    menu()
    _p('quitting main_DOX')
    time.sleep(1)


if __name__ == '__main__':
    main()

