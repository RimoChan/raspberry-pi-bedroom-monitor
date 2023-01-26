import os
import sys
from prometheus_client import start_http_server, Gauge


_entry = os.path.basename(sys.argv[0])

gauge_dict = {}
def save(key: str, value, tags: dict[str, str] = {}):
    tags = tags.copy()
    tags['entry'] = _entry
    if key not in gauge_dict:
        gauge_dict[key] = Gauge(f'pi_{key}', f'pi.{key}', labelnames=[*tags.keys()])
    if tags:
        gauge_dict[key].labels(**tags).set(value)
    else:
        gauge_dict[key].set(value)
