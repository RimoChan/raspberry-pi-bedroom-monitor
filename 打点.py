from prometheus_client import start_http_server, Gauge


gauge_dict = {}
def save(key: str, value, tags: dict[str, str] = {}):
    if key not in gauge_dict:
        gauge_dict[key] = Gauge(f'pi_{key}', f'pi.{key}', labelnames=[*tags.keys()])
    if tags:
        gauge_dict[key].labels(**tags).set(value)
    else:
        gauge_dict[key].set(value)
