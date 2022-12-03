import sys
import time
import math
import struct
import smbus
# import ctypes

# voc = ctypes.cdll.LoadLibrary('./voclib.so')

SGP40_CMD_FEATURE_SET = [0x20, 0x2F]
SGP40_CMD_MEASURE_TEST = [0X28,0X0E]
SGP40_CMD_SOFT_RESET = [0X00,0X06]
SGP40_CMD_HEATER_OFF = [0X36,0X15]
SGP40_CMD_MEASURE_RAW = [0X26,0X0F]
# SGP40_CMD_GET_SERIAL_ID = [0X36,0X82] #DATASHEET is not written ,but Sensirion have


CRC_TABLE = [
        0, 49, 98, 83, 196, 245, 166, 151, 185, 136, 219, 234, 125, 76, 31, 46,
        67, 114, 33, 16, 135, 182, 229, 212, 250, 203, 152, 169, 62, 15, 92, 109,
        134, 183, 228, 213, 66, 115, 32, 17, 63, 14, 93, 108, 251, 202, 153, 168,
        197, 244, 167, 150, 1, 48, 99, 82, 124, 77, 30, 47, 184, 137, 218, 235,
        61, 12, 95, 110, 249, 200, 155, 170, 132, 181, 230, 215, 64, 113, 34, 19,
        126, 79, 28, 45, 186, 139, 216, 233, 199, 246, 165, 148, 3, 50, 97, 80,
        187, 138, 217, 232, 127, 78, 29, 44, 2, 51, 96, 81, 198, 247, 164, 149,
        248, 201, 154, 171, 60, 13, 94, 111, 65, 112, 35, 18, 133, 180, 231, 214,
        122, 75, 24, 41, 190, 143, 220, 237, 195, 242, 161, 144, 7, 54, 101, 84,
        57, 8, 91, 106, 253, 204, 159, 174, 128, 177, 226, 211, 68, 117, 38, 23,
        252, 205, 158, 175, 56, 9, 90, 107, 69, 116, 39, 22, 129, 176, 227, 210,
        191, 142, 221, 236, 123, 74, 25, 40, 6, 55, 100, 85, 194, 243, 160, 145,
        71, 118, 37, 20, 131, 178, 225, 208, 254, 207, 156, 173, 58, 11, 88, 105,
        4, 53, 102, 87, 192, 241, 162, 147, 189, 140, 223, 238, 121, 72, 27, 42,
        193, 240, 163, 146, 5, 52, 103, 86, 120, 73, 26, 43, 188, 141, 222, 239,
        130, 179, 224, 209, 70, 119, 36, 21, 59, 10, 89, 104, 255, 206, 157, 172
        ]

#Without_humidity_compensation
#sgp40_measure_raw + 2*humi + CRC + 2*temp + CRC
WITHOUT_HUM_COMP = [0X26, 0X0F, 0X80, 0X00, 0XA2, 0X66, 0X66, 0X93] # default Temperature=25 Humidity=50
WITH_HUM_COMP = [0x26, 0x0f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00] #Manual input

ADDR = 0x59

class SGP40:
    def __init__(self, address=ADDR):
        self.i2c = smbus.SMBus(1)
        self.address = address
        
        # feature set 0x3220
        self.write(SGP40_CMD_FEATURE_SET)    
        time.sleep(0.25)
        Rbuf = self.Read() 
        # print('feature set:%#x'% ((int(Rbuf[0]) << 8) | Rbuf[1]))
        if ((int(Rbuf[0]) << 8) | Rbuf[1]) != 0x3220:
            raise RuntimeError("Self test failed")
        
        # Self Test 0xD400      
        self.write(SGP40_CMD_MEASURE_TEST)    
        time.sleep(0.25)
        Rbuf = self.Read()
        # print('Self Test  :%#x'% ((int(Rbuf[0]) << 8) | Rbuf[1]))
        if ((int(Rbuf[0]) << 8) | Rbuf[1]) != 0xD400: #0x4B00 is failed,0xD400 pass
            raise RuntimeError("Self test failed")
            
        # reset
        # self.write(SGP40_CMD_SOFT_RESET)

    def Read(self):
        return self.i2c.read_i2c_block_data(self.address, 0, 3)#last byte is CRC8
    
    def write(self, cmd):
        self.i2c.write_byte_data(self.address, cmd[0], cmd[1])
        
    def write_block(self, cmd):
        self.i2c.write_i2c_block_data(self.address, cmd[0], cmd[1:8])
        
    def raw(self):
        """The raw gas value"""
        # recycle a single buffer
        self.write_block(WITHOUT_HUM_COMP)
        time.sleep(0.25)
        Rbuf = self.Read()
        return ((int(Rbuf[0]) << 8) | Rbuf[1])
        
    def measureRaw(self, temperature, humidity):
        # 2*humi + CRC
        #paramh = struct.pack(">H", math.ceil(humidity * 0xffff / 100))
        h = humidity * 0xffff / 100
        paramh = (h >> 8, h & 0xff)
        crch = self.__crc(paramh[0], paramh[1])
        
        # 2*temp + CRC
        #paramt = struct.pack(">H", math.ceil((temperature + 45) * 0xffff / 175))
        t = (temperature + 45) * 0xffff / 175
        paramt = (t >> 8, t & 0xff)
        crct = self.__crc(paramt[0], paramt[1])
        
        WITH_HUM_COMP[2:3] = paramh
        WITH_HUM_COMP[4] = int(crch)
        WITH_HUM_COMP[5:6] = paramt
        WITH_HUM_COMP[7] = int(crct)
        #print(WITH_HUM_COMP)
        self.write_block(WITH_HUM_COMP)
        
        time.sleep(0.5)
        Rbuf = self.Read()
        # print(Rbuf)
        return ((int(Rbuf[0]) << 8) | Rbuf[1])
        
    def __crc(self, msb, lsb):
        crc = 0xff
        crc ^= msb
        crc = CRC_TABLE[crc]
        if lsb is not None:
            crc ^= lsb
            crc = CRC_TABLE[crc]
        return crc

if __name__ == '__main__':
    sgp = SGP40()
    time.sleep(1)
    try:
        while True:
            # print("Raw Gas: ", sgp.raw())
            print("measureRaw Gas: %d" %sgp.measureRaw(25, 50))
            
            time.sleep(1)

    except KeyboardInterrupt:
        exit()
