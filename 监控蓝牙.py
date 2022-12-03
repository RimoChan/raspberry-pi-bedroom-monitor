import time
from functools import lru_cache

import bluetooth._bluetooth as _bt

from 打点 import start_http_server, save, gauge_dict

from 别人的代码.inquiry_with_rssi import sock, device_inquiry_with_with_rssi
from utils import 冷却时间

start_http_server(9194)


@lru_cache(maxsize=1024)
def 查询名字(addr: str) -> str:
    timeoutms = int(10 * 1000)
    return _bt.hci_read_remote_name (sock, addr, timeoutms)


@冷却时间(30)
def 上报蓝牙():
    nearby_devices = device_inquiry_with_with_rssi(sock)
    l = []
    for addr, rssi in nearby_devices:
        try:
            name = 查询名字(addr)
        except _bt.error:
            continue
        l.append([addr, rssi, name])
    if 'bluetooth_rssi' in gauge_dict:
        gauge_dict['bluetooth_rssi'].clear()
    for addr, rssi, name in l:
        save('bluetooth_rssi', rssi, {'name': name, 'addr': addr})


while True:
    上报蓝牙()
    time.sleep(0.1)
