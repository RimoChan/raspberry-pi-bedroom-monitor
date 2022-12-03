import time
import logging
import requests

import 扫描wifi
import 扫描局域网

from 打点 import start_http_server, save, gauge_dict
from utils import 冷却时间


start_http_server(9192)


def requests_time(urls):
    d = {}
    for u in urls:
        try:
            a = time.time()
            assert requests.get(u, timeout=3).status_code == 200
            d[u] = time.time()-a
        except Exception:
            d[u] = None
    return d


@冷却时间(30)
def 上报wifi():
    all_wifi = 扫描wifi.get_wifi()
    if 'wifi_quality' in gauge_dict:
        gauge_dict['wifi_quality'].clear()
    for d in all_wifi.values():
        save('wifi_quality', d['quality'], {'essid': d['essid'], 'frequency': d['frequency']})
    if 'wifi_channel' in gauge_dict:
        gauge_dict['wifi_channel'].clear()
    for d in all_wifi.values():
        save('wifi_channel', d['channel'], {'essid': d['essid'], 'frequency': d['frequency']})


@冷却时间(60, left=10)
def 上报局域网():
    局域网机器 = 扫描局域网.扫描()
    if 'local_ip_rtt' in gauge_dict:
        gauge_dict['local_ip_rtt'].clear()
    for ip, d in 局域网机器.items():
        if d['avg_rtt'] is not None:
            save('local_ip_rtt', d['avg_rtt'], {'hostname': d['hostname'], 'ip': ip})


@冷却时间(60, left=20)
def 上报互联网():
    request_url_times = requests_time(['https://www.baidu.com/', 'https://github.com/', 'https://grafana.com/', 'https://cloudflare.com/'])
    if 'request_url_times' in gauge_dict:
        gauge_dict['request_url_times'].clear()
    for url, t in request_url_times.items():
        if t is not None:
            save('request_url_times', t, {'url': url})


while True:
    上报wifi()
    上报局域网()
    上报互联网()
    time.sleep(0.1)
