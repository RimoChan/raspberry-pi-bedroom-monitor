import time
import logging
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import board
import adafruit_scd4x

from 别人的代码 import ICM20948
from 别人的代码 import BME280
from 别人的代码 import LTR390
from 别人的代码 import TSL2591
from 别人的代码.DFRobot_SGP40 import DFRobot_SGP40

from 打点 import start_http_server, save
from utils import 冷却时间


start_http_server(9191)

bme280 = BME280.BME280()
bme280.get_calib_param()
light = TSL2591.TSL2591()
uv = LTR390.LTR390()
sgp = DFRobot_SGP40()
icm20948 = ICM20948.ICM20948()

源 = None

i2c = board.I2C()
scd4x = adafruit_scd4x.SCD4X(i2c)
scd4x.start_periodic_measurement()

sgp.begin(duration=15)
pool = ThreadPoolExecutor(max_workers=64)


@冷却时间(1)
def 上报传感器():
    global 源
    try:
        [bme280_pressure, bme280_temp, bme280_hum], lux, UVS, voc, icm = pool.map(lambda x: x(), [bme280.readData, light.Lux, uv.UVS, sgp.get_voc_index, icm20948.getdata])
        sgp.set_envparams(bme280_hum, bme280_temp)
        scd4x_co2, scd4x_temperature, scd4x_relative_humidity = scd4x.CO2, scd4x.temperature, scd4x.relative_humidity

        icm[3] /= 16384
        icm[4] /= 16384
        icm[5] /= 16384
        icm[9] *= 0.15
        icm[10] *= 0.15
        icm[11] *= 0.15
        icm = np.array(icm)
        新 = np.array([bme280_pressure, bme280_temp, bme280_hum, lux, UVS, voc, icm, scd4x_co2, scd4x_temperature, scd4x_relative_humidity], dtype=object)
        if 源 is None:
            源 = 新
        else:
            源 = 源*0.875 + 新*0.125
        bme280_pressure, bme280_temp, bme280_hum, lux, UVS, voc, icm, scd4x_co2, scd4x_temperature, scd4x_relative_humidity = 源
        save('pressure', bme280_pressure, {'sensor': 'bme280'})
        save('temperature', bme280_temp, {'sensor': 'bme280'})
        save('humidity', bme280_hum, {'sensor': 'bme280'})
        save('co2', scd4x_co2, {'sensor': 'scd4x'})
        save('temperature', scd4x_temperature, {'sensor': 'scd4x'})
        save('humidity', scd4x_relative_humidity, {'sensor': 'scd4x'})
        save('luminance', lux, {'sensor': 'TSL2591'})
        save('uv', UVS, {'sensor': 'LTR390'})
        save('voc', voc, {'sensor': 'sgp40'})
        save('roll', icm[0], {'axis': 'x'})
        save('roll', icm[1], {'axis': 'y'})
        save('roll', icm[2], {'axis': 'z'})
        save('acceleration', icm[3], {'axis': 'x'})
        save('acceleration', icm[4], {'axis': 'y'})
        save('acceleration', icm[5], {'axis': 'z'})
        save('gyroscope', icm[6], {'axis': 'x'})
        save('gyroscope', icm[7], {'axis': 'y'})
        save('gyroscope', icm[8], {'axis': 'z'})
        save('magnetic', icm[9], {'axis': 'x'})
        save('magnetic', icm[10], {'axis': 'y'})
        save('magnetic', icm[11], {'axis': 'z'})
    except Exception as e:
        logging.exception(e)


while True:
    上报传感器()
    time.sleep(0.1)
