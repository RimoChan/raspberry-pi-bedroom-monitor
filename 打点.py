import socket
from prometheus_client import start_http_server, Gauge


_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_s.connect(('1', 1))
_local_ip_address = _s.getsockname()[0]

gauge_dict = {}
def save(key: str, value, tags: dict[str, str] = {}):
    tags = tags.copy()
    tags['local_ip'] = _local_ip_address
    if key not in gauge_dict:
        gauge_dict[key] = Gauge(f'pi_{key}', f'pi.{key}', labelnames=[*tags.keys()])
    if tags:
        gauge_dict[key].labels(**tags).set(value)
    else:
        gauge_dict[key].set(value)
