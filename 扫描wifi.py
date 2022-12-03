import re
import time
import subprocess

import requests
# from rimo_storage.cache import disk_cache


def _scan() -> tuple[str, str]:
    r = subprocess.run(['sudo', 'iwlist', 'wlan0', 'scan'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    s = r.stdout.decode()
    err = r.stderr.decode()
    return s, err


def get_wifi() -> dict[str]:
    s, err = _scan()
    if 'Device or resource busy' in err:
        time.sleep(0.5)
        s, err = _scan()
    d = {}
    for i, ss in enumerate(re.split('Cell \d+ - ', s)[1:]):
        address = re.findall('Address: (.*?)\n', ss)[0]
        channel = re.findall('Channel:(.*?)\n', ss)[0]
        essid = (re.findall('ESSID:"(.*?)"', ss)+[''])[0]
        if not essid:
            essid = 'unknown_' + address.replace(':', '')
        frequency = float((re.findall('Frequency:(.*?) GHz', ss)+['0'])[0])
        quality = int((re.findall('Quality=(.*?)/70', ss)+['0'])[0])
        signal_level = int((re.findall('Signal level=(.*?) dBm', ss)+['0'])[0])
        d[address] = {
            'essid': essid,
            'frequency': frequency,
            'quality': quality,
            'channel': channel,
        }
    return d


def mac_to_location(mac: str):
    t = requests.get(f'http://api.cellocation.com:83/wifi/?mac={mac}&output=json')
    t.raise_for_status()
    j = t.json()
    if code := j['errcode']:
        if code == 10001:
            return None
        raise Exception(j)
    return j
