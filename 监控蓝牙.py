import time
from functools import lru_cache

import bluetooth._bluetooth as _bt

import yaml
import adafruit_ble
from adafruit_ble.advertising.standard import Advertisement

from 打点 import start_http_server, save, gauge_dict

from 别人的代码.inquiry_with_rssi import sock, device_inquiry_with_with_rssi
from utils import 冷却时间


ble = adafruit_ble.BLERadio()  
with open('company_identifiers.yaml') as f:
    company_identifiers = yaml.safe_load(f)
company_identifiers = {i['value']: i['name'] for i in company_identifiers['company_identifiers']}

start_http_server(9194)


@lru_cache(maxsize=1024)
def 查询名字(addr: str) -> str:
    timeoutms = int(10 * 1000)
    return _bt.hci_read_remote_name (sock, addr, timeoutms)


@冷却时间(30)
def 上报蓝牙():
    nearby_devices = device_inquiry_with_with_rssi(sock)
    print(nearby_devices)
    l = []
    for addr, rssi in nearby_devices:
        try:
            name = 查询名字(addr)
        except _bt.error:
            name = addr
        l.append([addr, rssi, name, 'None'])
    for adv in ble.start_scan(Advertisement, timeout=10):
        company = 'None'
        if 255 in adv.data_dict:
            company_id = int.from_bytes(adv.data_dict[255][:2], 'little')
            company = company_identifiers.get(company_id, 'None')
        l.append([adv.address.string, adv._rssi, adv.short_name or adv.complete_name or adv.address.string, company])
    if 'bluetooth_rssi' in gauge_dict:
        gauge_dict['bluetooth_rssi'].clear()
    for addr, rssi, name, company in l:
        save('bluetooth_rssi', rssi, {'name': name, 'addr': addr, 'company': company})


while True:
    上报蓝牙()
    time.sleep(0.1)
