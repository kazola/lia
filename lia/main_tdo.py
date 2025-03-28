import os.path
import sys
import time

import setproctitle
from lsb.cmd import (
    get_rx,
    cmd_gfv,
    cmd_sws,
    cmd_sts,
    cmd_gtm,
    cmd_stm,
    cmd_frm,
    cmd_wli,
    cmd_fds,
    cmd_bat,
    cmd_dns,
    cb_rx_noti,
    cmd_rws,
    cmd_scf,
    cmd_scc
)
from lsb.connect import (
    connect_mac,
    my_disconnect,
)
from lsb.li import (
    UUID_S,
    UUID_T
)
import toml
from lia.common import (
    clear_screen,
    create_app_data_folder_and_file,
    FILE_LOGGERS_TOML,
    open_text_editor,
    scan_for_tdo_loggers,
    get_sn_in_file_from_mac,
    get_remote_loggers_file,
    check_sn_format, print_menu_option
)
from lia.scf import prf_d
from rich.console import Console


console = Console()
prf_i = 0
BAT_FACTOR_TDO = 0.5454
g_app_cfg = {
    'rerun': False,
}


def _e(e):
    if get_rx():
        return
    raise Exception(f'error TDO: {e}')


def _p(s, t=0):
    print(('\t' * t) + s)


def _pt(s):
    return _p(s, t=1)


def _deploy_one_tdo_logger(p, sn):

    mac = p.address()

    _p(f'\nDeploying TDO logger {sn} mac {mac}')

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

    cmd_dns(p, 'LAB')
    _e('command deployment name')

    cmd_fds(p)
    _e('command first deployment set')

    v = cmd_bat(p)
    _e('command bat')
    v /= BAT_FACTOR_TDO
    _pt(f'bat = {int(v)} mV')

    if ver >= "4.0.06":
        d = prf_d[prf_i][1]
        # send SCC tags
        for tag, v in d.items():
            if tag == 'RVN':
                continue
            _pt(f'scf {tag} {v}')
            cmd_scf(p, tag, v)
            _e(f'command scf {tag} {v}')
            time.sleep(.1)
        # send the hardcoded DHU
        cmd_scc(p, 'DHU', '00101')
        _e(f'command scc dhu')
        time.sleep(.1)

    if g_app_cfg['rerun']:
        if not cmd_rws(p, g):
            _e('command run with string')
        _pt('run with string OK')

    my_disconnect(p)
    _pt('disconnected')


def menu():
    create_app_data_folder_and_file()
    ls_pp = []
    c = ''

    while 1:

        clear_screen()

        # we not always do a scan
        skip_scan = c in ('p', 'r', 'e')
        if not skip_scan:
            ls_pp = scan_for_tdo_loggers()

        # read loggers file
        d_lf = {}
        if os.path.exists(FILE_LOGGERS_TOML):
            d_lf = toml.load(FILE_LOGGERS_TOML)['loggers']
        bn = os.path.basename(FILE_LOGGERS_TOML)

        # analyze loggers file and get basename
        if len(d_lf) == 0:
            console.print(
                f'* Warning: your file {bn} contains 0 loggers',
                style='yellow'
            )

        # build menu
        global prf_i
        m = {
            's': f'scan again for TDO loggers',
            'p': f'set profiler ({prf_d[prf_i][0]})',
            'r': f'set run flag ({g_app_cfg["rerun"]})',
            'e': f'edit file {bn} ({len(d_lf)})',
            'q': 'quit'
        }

        # display menu
        _p('\nSelect an option...')
        for k, v in m.items():
            if not k.isnumeric():
                print_menu_option(k, v)

        # display list of deployable TDO loggers
        ls_file_macs = [m.lower() for m in d_lf.values()]
        ls_pp = [p for p in ls_pp if p.address().lower() in ls_file_macs ]
        if ls_pp:
            _p('\n... or deploy one of the TDO loggers detected nearby:')
            for i, per in enumerate(ls_pp):
                sn_or_mac = get_sn_in_file_from_mac(d_lf, per.address())
                print_menu_option(i, f'deploy {sn_or_mac}')
                # add to menu dictionary
                m[str(i)] = per.address()

        # grab user choice
        c = input('\n-> ')
        if c not in m.keys():
            continue

        if c == 'q':
            break

        if c == 'p':
            prf_i = (prf_i + 1) % len(prf_d)
            continue

        if c == 'r':
            g_app_cfg['rerun'] = not g_app_cfg['rerun']
            continue

        if c == 's':
            # just go at it again
            continue

        if c == 'e':
            create_app_data_folder_and_file()
            open_text_editor()
            continue

        if not c.isnumeric():
            continue

        # ----------------------------------------------------
        # deploy TDO logger indicated by number input by user
        # ----------------------------------------------------

        my_p = ls_pp[int(c)]
        try:
            mac = my_p.address()
            sn = get_sn_in_file_from_mac(d_lf, mac)
            if check_sn_format(sn):
                _deploy_one_tdo_logger(my_p, sn)
                _p(f'\nDeployment of TDO logger {sn} went OK!')
            else:
                _p(f'\nerror: bad SN ({sn}) for mac {mac}')
        except (Exception,) as ex:
            _p(f'\nerror: {ex}')

        try:
            my_disconnect(my_p)
        except (Exception,) as ex:
            _p(f'\nerror disconnecting: {ex}')

        console.print('\npress ENTER to go back to menu', style='grey')
        input()


def main():
    if len(sys.argv) == 2:
        # online mode
        get_remote_loggers_file()

    menu()


if __name__ == '__main__':
    setproctitle.setproctitle('main_tdo')
    main()
