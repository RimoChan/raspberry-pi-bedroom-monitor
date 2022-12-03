import sys
import time
import math
import smbus
import RPi.GPIO as GPIO

ADDR                = (0x29)

COMMAND_BIT         = (0xA0)
#Register (0x00)
ENABLE_REGISTER     = (0x00)
ENABLE_POWERON      = (0x01)
ENABLE_POWEROFF     = (0x00)
ENABLE_AEN          = (0x02)
ENABLE_AIEN         = (0x10)
ENABLE_SAI          = (0x40)
ENABLE_NPIEN        = (0x80)

CONTROL_REGISTER    = (0x01)
SRESET              = (0x80)

AILTL_REGISTER      = (0x04)
AILTH_REGISTER      = (0x05)
AIHTL_REGISTER      = (0x06)
AIHTH_REGISTER      = (0x07)
NPAILTL_REGISTER    = (0x08)
NPAILTH_REGISTER    = (0x09)
NPAIHTL_REGISTER    = (0x0A)
NPAIHTH_REGISTER    = (0x0B)

PERSIST_REGISTER    = (0x0C)
# Bits 3:0
# 0000          Every ALS cycle generates an interrupt
# 0001          Any value outside of threshold range
# 0010          2 consecutive values out of range
# 0011          3 consecutive values out of range
# 0100          5 consecutive values out of range
# 0101          10 consecutive values out of range
# 0110          15 consecutive values out of range
# 0111          20 consecutive values out of range
# 1000          25 consecutive values out of range
# 1001          30 consecutive values out of range
# 1010          35 consecutive values out of range
# 1011          40 consecutive values out of range
# 1100          45 consecutive values out of range
# 1101          50 consecutive values out of range
# 1110          55 consecutive values out of range
# 1111          60 consecutive values out of range

ID_REGISTER         = (0x12)

STATUS_REGISTER     = (0x13)#read only

CHAN0_LOW           = (0x14)
CHAN0_HIGH          = (0x15)
CHAN1_LOW           = (0x16)
CHAN1_HIGH          = (0x17)

LUX_DF = 408.0
LUX_COEFB = 1.64
LUX_COEFC = 0.59
LUX_COEFD = 0.86

#AGAIN
LOW_AGAIN           = (0X00)#Low gain (1x)
MEDIUM_AGAIN        = (0X10)#Medium gain (25x)
HIGH_AGAIN          = (0X20)#High gain (428x)
MAX_AGAIN           = (0x30)#Max gain (9876x)

#ATIME
ATIME_100MS         = (0x00)#100 millis #MAX COUNT 36863 
ATIME_200MS         = (0x01)#200 millis #MAX COUNT 65535 
ATIME_300MS         = (0x02)#300 millis
ATIME_400MS         = (0x03)#400 millis
ATIME_500MS         = (0x04)#500 millis
ATIME_600MS         = (0x05)#600 millis

MAX_COUNT_100MS     = (36863) # 0x8FFF
MAX_COUNT           = (65535) # 0xFFFF

# int pin
INI_PIN = 23

class TSL2591:
    def __init__(self, address=ADDR):
        self.i2c = smbus.SMBus(1)
        self.address = address

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(INI_PIN, GPIO.IN)

        self.ID = self.Read_Byte(ID_REGISTER)
        if(self.ID != 0x50):
            print("ID = 0x%x"%self.ID)
            sys.exit()

        # self.Write_Byte(ENABLE_REGISTER, ENABLE_POWERON | ENABLE_AEN)
        self.Write_Byte(ENABLE_REGISTER, ENABLE_AIEN | ENABLE_POWERON | ENABLE_AEN | ENABLE_NPIEN)
        self.IntegralTime = ATIME_200MS
        self.Gain = MEDIUM_AGAIN
        self.Write_Byte(CONTROL_REGISTER, self.IntegralTime | self.Gain)
        self.Write_Byte(PERSIST_REGISTER, 0x01)
        # self.Write_Byte(0xE7, 0x13)
        atime = 100.0 * self.IntegralTime + 100.0
        again = 1.0
        if self.Gain == MEDIUM_AGAIN:
            again = 25.0
        elif self.Gain == HIGH_AGAIN:
            again = 428.0
        elif self.Gain == MAX_AGAIN:
            again = 9876.0
        self.Cpl = (atime * again) / LUX_DF

    def Read_Byte(self, Addr):
        Addr = (COMMAND_BIT | Addr) & 0xFF
        return self.i2c.read_byte_data(self.address, Addr)

    def Write_Byte(self, Addr, val):
        Addr = (COMMAND_BIT | Addr) & 0xFF
        self.i2c.write_byte_data(self.address, Addr, val & 0xFF)

    def Read_2Channel(self):
        CH0L = self.Read_Byte(CHAN0_LOW)
        CH0H = self.Read_Byte(CHAN0_LOW + 1)
        CH1L = self.Read_Byte(CHAN0_LOW + 2)
        CH1H = self.Read_Byte(CHAN0_LOW + 3)
        full = (CH0H << 8)|CH0L
        ir = (CH1H << 8)|CH1L
        return full,ir

    def Lux(self):
        status = self.Read_Byte(0x13)
        if(status & 0x10):
            # print ('soft goto interrupt')
            self.Write_Byte(0xE7, 0x13)
        
        # if(GPIO.input(INI_PIN) == 1):
            # print("----------------")
            # print ('hard goto interrupt')
            
        full, ir = self.Read_2Channel()
        if full == 0xFFFF or ir == 0xFFFF:
            raise RuntimeError('Numerical overflow!')

        # lux1 = (full - (LUX_COEFB * ir)) / self.Cpl
        # lux2 = ((LUX_COEFC * full) - (LUX_COEFD * ir)) / self.Cpl
        # return max(int(lux1), int(lux2))
        if full == 0:
            return 0
        lux = ((full-ir) * (1.00 - (ir/full))) / self.Cpl
        # lux = (full-ir)/ self.Cpl
        return lux

    def SET_LuxInterrupt(self, SET_LOW, SET_HIGH):
        full, ir = self.Read_2Channel()
        set0dataL = int(SET_LOW * self.Cpl + ir)
        set0dataH = int(SET_HIGH * self.Cpl + ir)

        self.Write_Byte(AILTL_REGISTER, set0dataL & 0xFF)
        self.Write_Byte(AILTH_REGISTER, set0dataL >> 8)

        self.Write_Byte(AIHTL_REGISTER, set0dataH & 0xFF)
        self.Write_Byte(AIHTH_REGISTER, set0dataH >> 8)


if __name__ == '__main__':
    sensor = TSL2591()
    # sensor.SET_LuxInterrupt(20, 200)
    time.sleep(1)
    try:
        while True:
            lux = sensor.Lux()
            print("Lux: %d" %lux)
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        # sensor.Disable()
        exit()
