import os.path
import setproctitle
from lsb.cmd import (
    get_rx,
    cmd_sws,
    cmd_frm,
    cb_rx_noti,
    cmd_dir,
    cmd_dwg,
    cmd_dwl
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
    check_sn_format,
    print_menu_option,
    file_dl_path,
    scan_for_all_loggers,
    filter_by_loggers_file,
    scan_for_dox_loggers,
    scan_for_tdo_loggers
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


def _download_one_logger(p, sn):

    mac = p.address()

    _p(f'\ndeploying {g_info} logger {sn} mac {mac}')

    if not connect_mac(p, mac):
        _e('connecting')
    p.notify(UUID_S, UUID_T, cb_rx_noti)

    # start sending commands
    g = ("-3.333333", "-4.444444", None, None)
    cmd_sws(p, g)
    _e('command stop with string')
    _pt('stop OK')

    # get list of logger files
    rv = cmd_dir(p)
    _e('command DIR')
    ls = rv['ls']
    for name, size in ls.items():
        _p(f'downloading {name}, {size} bytes')
        cmd_dwg(p, name)
        _e(f'command DWG file {name}')
        bb = cmd_dwl(p, name, size)
        _e(f'command DWL file {name}')

        # todo ---> do the progress bar
        with open(file_dl_path(name), 'wb') as f:
            f.write(bb)
        _p(f'file {name} download OK!')

    # reset logger file-system
    cmd_frm(p)
    _e('command format')
    _pt('format OK')

    my_disconnect(p)
    _pt('disconnected')


def menu():
    create_app_data_folder_and_file()
    ls_pp = []
    c = ''
    global g_info
    global g_cfg

    while 1:

        clear_screen()

        # we not always do a scan
        skip_scan = c in ('e', )
        if not skip_scan:
            if g_cfg['type'] == 0:
                ls_pp = scan_for_all_loggers()
            elif g_cfg['type'] == 1:
                ls_pp = scan_for_dox_loggers()
            else:
                ls_pp = scan_for_tdo_loggers()

        # read loggers file
        d_lf = {}
        if os.path.exists(FILE_LOGGERS_TOML):
            d_lf = toml.load(FILE_LOGGERS_TOML)['loggers']
        bn = os.path.basename(FILE_LOGGERS_TOML)

        # filter or not filter
        if g_cfg['filter']:
            ls_pp = filter_by_loggers_file(ls_pp, d_lf)

        # build menu
        ty = {0: 'ALL', 1: 'DOX', 2: 'TDO'}
        m = {
            's': f'scan again',
            't': f'set type ({ty[g_cfg["type"]]})',
            'f': f'filter by loggers file ({g_cfg["filter"]})',
            'e': f'edit file {bn} ({len(d_lf)})',
            'q': 'quit'
        }

        # display menu
        _p('\nSelect an option...')
        for k, v in m.items():
            if not k.isnumeric():
                print_menu_option(k, v)

        # try to re-order by type
        ls_pp.sort(key=lambda p: p.identifier())

        # display list of deployable TDO loggers
        if ls_pp:
            _p('\n... or download one of the loggers detected nearby:')
            for i, per in enumerate(ls_pp):
                sn_or_mac = get_sn_in_file_from_mac(d_lf, per.address())
                info = per.identifier().replace('-', '')
                print_menu_option(i, f'download {info} {sn_or_mac}')
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
            sn = get_sn_in_file_from_mac(d_lf, mac)
            if check_sn_format(sn):
                _download_one_logger(my_p, sn)
                _p(f'\ndownload of {g_info} logger {sn} went OK!')
            else:
                _p(f'\nerror: bad SN ({sn}) for mac {mac}')
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
