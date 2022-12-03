import time
import psutil
from 打点 import start_http_server, save
from utils import 冷却时间


start_http_server(9195)


@冷却时间(15)
def 上报cpu温度():
    cpu_temperature = float(open("/sys/class/thermal/thermal_zone0/temp").read()) / 1000
    save('cpu_temperature', cpu_temperature)


while True:
    上报cpu温度()
    time.sleep(0.1)
