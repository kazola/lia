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
    my_disconnect, get_adapters
)
from lsb.li import (
    UUID_S,
    UUID_T
)
from common import clear_screen, PLATFORM
from scf import prf_d


prf_i = 0
BAT_FACTOR_TDO = 0.5454
TIMEOUT_SCAN_MS = 10000
ad = get_adapters()[0]


def _e(e):
    if get_rx():
        return
    raise Exception(f'error: {e}')


def _p(s):
    print(s)


def scan_for_loggers(info, t=TIMEOUT_SCAN_MS):
    assert len(info) == 3
    print(f'scan for {info} loggers during {t} ms')
    ad.scan_for(t)
    ls_pp = ad.scan_get_results()
    ls_pp = [p for p in ls_pp if p.identifier() == info]
    return ls_pp



def _deploy_one_tdo_logger(p):

    mac = p.address()
    sn = 1234567

    # todo ---> obtain SN from database

    _p(f'trying to deploy logger {sn} mac {mac}')

    if not connect_mac(p, mac):
        _e('connecting')
    p.notify(UUID_S, UUID_T, cb_rx_noti)

    # start sending commands
    ver = cmd_gfv(p)
    _e('command version')
    ver = ver[6:].decode()
    _p(f'version {ver}')

    g = ("-3.333333", "-4.444444", None, None)
    cmd_sws(p, g)
    _e('command stop with string')
    _p('stop OK')

    v = cmd_sts(p)
    _e('command status')
    _p(f'status {v}')

    v = cmd_gtm(p)
    _e('command get_time')
    _p(f'get time {v}')

    cmd_stm(p)
    _e('command set time')
    _p(f'set time OK')

    cmd_frm(p)
    _e('command format')
    _p('format OK')

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
    _p(f'bat = {v} mV')

    if ver >= "4.0.06":
        d = prf_d[prf_i][1]
        for tag, v in d.items():
            _p(f'scf {tag} {v}')
            cmd_scf(p, tag, v)
            _e(f'command scf {tag} {v}')
            time.sleep(.1)
        # send the hardcoded DHU
        cmd_scc(p, 'DHU', '00101')
        _e(f'command scc dhu')
        time.sleep(.1)


    # if not cmd_rws(p, g):
    #     _e('command run with string')
    # _p('run OK')

    my_disconnect(p)
    _p('disconnected')


def deploy_all_tdo_loggers():
    info = 'TDO'
    print('\n\n')
    print(f'Deploying {info} loggers under {PLATFORM}')
    ls = scan_for_loggers(info)
    if not ls:
        print(f'we did not find any {info} logger')
        return
    for p in ls:
        try:
            _deploy_one_tdo_logger(p)
        except (Exception, ) as ex:
            print(ex)
            my_disconnect(p)


def menu():
    global prf_i
    m = {
        's': 'scan again',
        'p': f'set profiling, currently {prf_d[prf_i][0]}',
        'q': 'quit'
    }
    clear_screen()
    _p('doing first scan...')
    ls = scan_for_loggers('TDO')

    # forever
    while 1:
        # display menu
        clear_screen()
        _p('Select an option:')
        for k, v in m.items():
            if not k.isnumeric():
                _p(f'\t{k}) {v}')
        if ls:
            print('\nvisible loggers:')
            for i, per in enumerate(ls):
                _p(f'\t{i}) {per.address()}')
                m[str(i)] = per.address()

        # grab user choice
        c = input()
        if c not in m.keys():
            continue
        if c == 'q':
            break
        if c == 's':
            ls = scan_for_loggers('TDO')
        if c == 'p':
            prf_i = (prf_i + 1) % len(prf_d)
            continue
        if not c.isnumeric():
            continue

        # deploy logger
        my_p = ls[int(c)]
        try:
            _deploy_one_tdo_logger(my_p)
            _p('went OK!')
        except (Exception,) as ex:
            _p(f'error: {ex}')
            my_disconnect(my_p)
        _p('\npress ENTER to go back to menu')
        input()


if __name__ == '__main__':
    menu()
    _p('quitting main_TDO')
    time.sleep(1)