import json
import os.path
import setproctitle
from lsb.cmd import (
    get_rx,
    cmd_sws,
    cmd_frm,
    cb_rx_noti,
    cmd_dir,
    cmd_dwg,
    cmd_dwl,
    cmd_mts,
    cmd_cfg
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
    get_sn_in_file_from_mac,
    print_menu_option,
    file_dl_path,
    scan_for_all_loggers,
    filter_by_loggers_file,
    scan_for_dox_loggers,
    scan_for_tdo_loggers,
    print_success
)
from rich.console import Console


console = Console()
g_info = ''
g_cfg = {
    'filter': False,
    'type': 0
}


def _e(e):
    if get_rx():
        return
    raise Exception(f'error {g_info}: {e}')


def _p(s, t=0):
    print(('\t' * t) + s)


def _pt(s):
    return _p(s, t=1)


def _download_one_logger(p):

    mac = p.address()

    _p(f'\nDownloading {g_info} logger {mac}')

    if not connect_mac(p, mac):
        _e('connecting')
    p.notify(UUID_S, UUID_T, cb_rx_noti)

    # start sending commands
    g = ("-3.333333", "-4.444444", None, None)
    cmd_sws(p, g)
    _e('command stop with string')
    _pt('stop OK')

    # debug, create dummy files
    # _pt('creating dummy file')
    # cmd_mts(p)
    # _e('command MTS')

    # get list of logger files
    rv = cmd_dir(p)
    _e('command DIR')
    ls = rv['ls']
    if not ls:
        _pt('no files to download from this logger')
    else:
        _pt('listing files in this logger:')
        for name, size in ls.items():
            _p(f'- {name}, {size} bytes', t=2)

    # download every file
    d_cmd_cfg = {}
    for name, size in ls.items():
        _pt(f'downloading {name}, {size} bytes...')
        cmd_dwg(p, name)
        _e(f'command DWG file {name}')
        bb = cmd_dwl(p, size)
        _e(f'command DWL file {name}')
        dl_path = file_dl_path(mac, name)
        with open(dl_path, 'wb') as f:
            f.write(bb)
        _pt(f'file {name} download OK')
        if name == 'MAT.cfg':
            with open(dl_path, 'r') as j_f:
                d_cmd_cfg = json.load(j_f)

    # reset logger file-system
    cmd_frm(p)
    _e('command format')
    _pt('format OK')

    # restore configuration file
    if d_cmd_cfg:
        cmd_cfg(p, d_cmd_cfg)
        _e('command CFG')
        _pt('CFG OK')


    my_disconnect(p)
    _pt('disconnected')


def menu():
    create_app_data_folder_and_file()
    ls_scan = []
    c = ''
    global g_info
    global g_cfg

    while 1:

        clear_screen()

        # we not always do a scan
        skip_scan = c in ('e', )
        if not skip_scan:
            if g_cfg['type'] == 0:
                ls_scan = scan_for_all_loggers()
            elif g_cfg['type'] == 1:
                ls_scan = scan_for_dox_loggers()
            else:
                ls_scan = scan_for_tdo_loggers()

        # read loggers file
        d_lf = {}
        if os.path.exists(FILE_LOGGERS_TOML):
            d_lf = toml.load(FILE_LOGGERS_TOML)['loggers']
        bn = os.path.basename(FILE_LOGGERS_TOML)

        # filter or not filter
        ls_pp = []
        if g_cfg['filter']:
            ls_pp = filter_by_loggers_file(ls_scan, d_lf)

        # build menu
        ty = {0: 'ALL', 1: 'DOX', 2: 'TDO'}
        m = {
            's': f'scan again',
            't': f'set type ({ty[g_cfg["type"]]})',
            'f': f'filter by loggers file ({g_cfg["filter"]})',
            'e': f'edit file {bn} ({len(d_lf)})',
            'c': f'create file {bn} dynamically',
            'q': 'quit'
        }

        # display menu
        _p('\nSelect an option...')
        for k, v in m.items():
            if not k.isnumeric():
                print_menu_option(k, v)

        # try to re-order by type
        ls_pp.sort(key=lambda x: x.identifier())

        # restrict to developer logger when debugging
        # ls_pp = [p for p in ls_pp if p.address().lower() == "d0:2e:ab:d9:29:48"]

        # display list of deployable TDO loggers
        if ls_pp:
            _p('\n... or download one of the loggers detected nearby:')
            for i, per in enumerate(ls_pp):
                sn_or_mac = get_sn_in_file_from_mac(d_lf, per.address())
                info = per.identifier().replace('-', '')
                print_menu_option(i, f'{info} {sn_or_mac}')
                # add to menu dictionary
                m[str(i)] = per.address()

        # grab user choice
        c = input('\n-> ')
        if c not in m.keys():
            continue

        if c == 'q':
            break

        if c == 's':
            # just go at it again
            continue
        
        if c == 'f':
            g_cfg['filter'] = not g_cfg['filter']

        if c == 'e':
            create_app_data_folder_and_file()
            open_text_editor()
            continue

        if c == 'c':
            _p('warning: this will overwrite your loggers file, sure?')
            if input('\n\t-> ') != 'y':
                continue
            with open(FILE_LOGGERS_TOML, 'w') as f:
                f.write('[loggers]\n')
                for p in ls_scan:
                    f.write(f'"{p.address()}" = ""\n')
            continue

        if c == 't':
            g_cfg['type'] = (g_cfg['type'] + 1) % 3

        if not c.isnumeric():
            continue

        # ----------------------------------------------------
        # deploy TDO logger indicated by number input by user
        # ----------------------------------------------------

        g_info = ''

        my_p = ls_pp[int(c)]
        try:
            mac = my_p.address()
            g_info = my_p.identifier()
            _download_one_logger(my_p)
            print_success(f'\nDownload of {g_info} logger {mac} went OK!')
        except (Exception,) as ex:
            _p(f'\nerror: {ex}')

        try:
            my_disconnect(my_p)
        except (Exception,) as ex:
            _p(f'\nerror disconnecting: {ex}')

        _p('\npress ENTER to go back to menu')
        input()


def main():
    menu()


if __name__ == '__main__':
    setproctitle.setproctitle('download')
    main()
