import socket
import ipaddress
from concurrent.futures import ThreadPoolExecutor

import netifaces
from icmplib import ping


_hostname_save = {}


def scan_ping(ip):
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        _hostname_save[ip] = hostname
    except Exception:
        hostname = None
    t = ping(ip, count=1)
    return hostname, t.is_alive, t.avg_rtt


def 扫描() -> dict[str]:
    好 = []
    for interface in netifaces.interfaces():
        for i in netifaces.ifaddresses(interface).values():
            for j in i:
                if j.get('netmask') == '255.255.255.0':
                    好.append(j)
    机器 = {}
    for i in 好:
        network = ipaddress.IPv4Network(f'{i["addr"]}/{i["netmask"]}', strict=False)
        all_ip = [str(ip) for ip in network]
        for a, [hostname, alive, avg_rtt] in zip(all_ip, [*ThreadPoolExecutor(max_workers=32).map(scan_ping, all_ip)]):
            if not alive and not hostname:
                continue
            if not alive and hostname:
                机器[a] = {'hostname': hostname, 'avg_rtt': None}
            if alive and not hostname:
                机器[a] = {'hostname': _hostname_save.get(a, a.replace('.', '_')), 'avg_rtt': avg_rtt}
            if alive and hostname:
                机器[a] = {'hostname': hostname, 'avg_rtt': avg_rtt}
    return 机器
