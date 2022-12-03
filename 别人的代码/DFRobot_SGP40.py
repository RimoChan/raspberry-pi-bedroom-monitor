""" 
  @file DFRobot_SGP40.py
  @note DFRobot_SGP40 Class infrastructure, implementation of underlying methods
  @copyright   Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
  @licence     The MIT License (MIT)
  @author      [yangfeng]<feng.yang@dfrobot.com> 
  version  V1.0
  date  2021-01-15
  @get from https://www.dfrobot.com
  @url https://github.com/DFRobot/DFRobot_SGP40
"""

import smbus
import time
from .DFRobot_SGP40_VOCAlgorithm import DFRobot_VOCAlgorithm

class DFRobot_SGP40:
    DFRobot_SGP40_ICC_ADDR                           = 0x59
    TEST_OK_H                                        = 0xD4
    TEST_OK_L                                        = 0x00
    CMD_HEATER_OFF_H                                 = 0x36
    CMD_HEATER_OFF_L                                 = 0x15
                                                     
    CMD_MEASURE_TEST_H                               = 0x28
    CMD_MEASURE_TEST_L                               = 0x0E
                                                     
    CMD_SOFT__reset_H                                = 0x00
    CMD_SOFT__reset_L                                = 0x06
                                                     
    CMD_MEASURE_RAW_H                                = 0x26
    CMD_MEASURE_RAW_L                                = 0x0F

    DURATION_READ_RAW_VOC                            = 0.03
    DURATION_WAIT_MEASURE_TEST                       = 0.25
    OFFSET                                           = 0x00
    '''
      @brief Module init
      @param bus:int Set to IICBus
      @param relative_humidity:float Set to relative_humidity
      @param temperature_c:float Set to temperature
    '''
    def __init__(self,bus = 1,relative_humidity = 50,temperature_c = 25):
        self.__i2cbus = smbus.SMBus(bus)
        self.__my_vocalgorithm = DFRobot_VOCAlgorithm()
        self.__i2c_addr = self.DFRobot_SGP40_ICC_ADDR
        self.__temperature_c = temperature_c
        self.__relative_humidity = relative_humidity
        self.__rh = 0
        self.__temc = 0
        self.__rh_h = 0
        self.__rh_l = 0
        self.__temc_h = 0
        self.__temc_l = 0
        self.__temc__crc = 0
        self.__rh__crc = 0

    '''
      @brief Set temperature and humidity
      @param relative_humidity:float Set to relative_humidity
      @param temperature_c:float Set to temperature
    '''
    def set_envparams(self,relative_humidity,temperature_c):
        self.__temperature_c = temperature_c
        self.__relative_humidity = relative_humidity

    '''
      @brief start equipment
      @param duration:int Set to Warm-up time
      @return equipment condition. 0: succeed  1: failed 
    '''
    def begin(self,duration = 10):
        self.__my_vocalgorithm.vocalgorithm_init()
        timeOne = int(time.time())
        while(int(time.time())-timeOne<duration):
            self.get_voc_index()
        return self.__measure_test()

    '''
      @brief Get raw data
      @param duration:int Set to Warm-up time
      @return collect result. (-1 collect failed)  (>0 the collection value)
    '''
    def measure_raw(self):
        self.__data_transform()
        self.__i2cbus.write_i2c_block_data(self.__i2c_addr,self.CMD_MEASURE_RAW_H, [self.CMD_MEASURE_RAW_L,self.__rh_h,self.__rh_l,self.__rh__crc,self.__temc_h,self.__temc_l,self.__temc__crc])
        time.sleep(self.DURATION_READ_RAW_VOC)
        raw = self.__i2cbus.read_i2c_block_data(self.__i2c_addr,self.OFFSET,3)
        if self.__check__crc(raw) == 0:
          return raw[0]<<8 | raw[1]
        else:
          return -1

    '''
      @brief Measure VOC index after humidity compensation
      @n VOC index can indicate the quality of the air directly. The larger the value, the worse the air quality.
      @n   0-100,no need to ventilate, purify
      @n   100-200,no need to ventilate, purify
      @n   200-400,ventilate, purify
      @n   00-500,ventilate, purify intensely
      @param duration:int Set to Warm-up time
      @return The VOC index measured, ranged from 0 to 500
    '''
    def get_voc_index(self):
        raw = self.measure_raw()
        if raw<0:
            return -1
        else:
            vocIndex = self.__my_vocalgorithm.vocalgorithm_process(raw)
            return vocIndex

    '''
      @brief Convert environment parameters
    '''
    def __data_transform(self):
        self.__rh = int(((self.__relative_humidity*65535)/100+0.5))
        self.__temc = int(((self.__temperature_c+45)*(65535/175)+0.5))
        self.__rh_h = int(self.__rh)>>8
        self.__rh_l = int(self.__rh)&0xFF
        self.__rh__crc = self.__crc(self.__rh_h,self.__rh_l)
        self.__temc_h = int(self.__temc)>>8
        self.__temc_l = int(self.__temc)&0xFF
        self.__temc__crc = self.__crc(self.__temc_h,self.__temc_l) 

    '''
      @brief Sensor self-test
      @n VOC index can indicate the quality of the air directly. The larger the value, the worse the air quality.
      @n   0-100,no need to ventilate, purify
      @n   100-200,no need to ventilate, purify
      @n   200-400,ventilate, purify
      @n   00-500,ventilate, purify intensely
      @param duration:int Set to Warm-up time
      @return self-test condition. 0: succeed; 1: failed 
    '''
    def __measure_test(self):
        self.__i2cbus.write_i2c_block_data(self.__i2c_addr,self.CMD_MEASURE_TEST_H, [self.CMD_MEASURE_TEST_L])
        time.sleep(self.DURATION_WAIT_MEASURE_TEST)
        raw = self.__i2cbus.read_i2c_block_data(self.__i2c_addr,self.OFFSET,2)
        if raw[0] == self.TEST_OK_H and raw[1] == self.TEST_OK_L :
            return 0
        else:
            return 1

    '''
      @brief Sensor reset
    '''
    def __reset(self):
        self.__i2cbus.write_i2c_block_data(self.__i2c_addr,self.CMD_SOFT__reset_H, [self.CMD_SOFT__reset_L])

    '''
      @brief spg40 Heater Off. Turn the hotplate off and stop the measurement. Subsequently, the sensor enters the idle mode.
    '''
    def __heater_off(self):
        self.__i2cbus.write_i2c_block_data(self.__i2c_addr,self.CMD_HEATER_OFF_H, [self.CMD_HEATER_OFF_L])

    '''
      @brief Verify the calibration value of the sensor
      @param raw : list Parameter to check
      @return  Check result. -1: Check failed; 0: Check succeed
    '''
    def __check__crc(self, raw):
        assert (len(raw) == 3)
        if self.__crc(raw[0], raw[1]) != raw[2]:
            return -1
        return 0

    '''
      @brief CRC
      @param data1  High 8 bits data
      @param data2  LOW 8 bits data
      @return  Calibration value
    '''
    def __crc(self,data_1,data_2):
        crc = 0xff
        list = [data_1,data_2]
        for i in range(0,2):
            crc = crc^list[i]
            for bit in range(0,8):
                if(crc&0x80):
                    crc = ((crc <<1)^0x31)
                else:
                    crc = (crc<<1)
            crc = crc&0xFF
        return crc
