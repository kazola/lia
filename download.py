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
    filter_by_loggers_file
)
from rich.console import Console


console = Console()
g_info = ''
g_cfg = {
    'filter': False
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

    while 1:

        clear_screen()

        # we not always do a scan
        skip_scan = c in ('e', 'f', )
        if not skip_scan:
            ls_pp = scan_for_all_loggers()

        # read loggers file
        d_lf = {}
        if os.path.exists(FILE_LOGGERS_TOML):
            d_lf = toml.load(FILE_LOGGERS_TOML)['loggers']
        bn = os.path.basename(FILE_LOGGERS_TOML)

        # filter or not filter
        global g_cfg
        if g_cfg['filter']:
            ls_pp = filter_by_loggers_file(ls_pp, d_lf)

        # build menu
        m = {
            's': f'scan again for ALL loggers',
            'f': f'filter by loggers file ({g_cfg["filter"]})',
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
            _p('\n... or download one of the loggers detected nearby:')
            for i, per in enumerate(ls_pp):
                sn_or_mac = get_sn_in_file_from_mac(d_lf, per.address())
                info = p.identifier().replace('-', '')
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

        if not c.isnumeric():
            continue

        # ----------------------------------------------------
        # deploy TDO logger indicated by number input by user
        # ----------------------------------------------------

        global g_info
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
