import machine as M
import utime   as T
import utils   as U

class BMX280:
    SLAVE_ADDR = 0x00 # can be 0x76 (if SDO = 0) or 0x77 (if SDO = 1)
    
    SLAVE_ADDR_LOW  = 0x76 # 0b01110110
    SLAVE_ADDR_HIGH = 0x77 # 0b01110111
       
    SLAVE_ADDR_WRITE = 0xEC
    SLAVE_ADDR_READ  = 0xED

    BME280_ID    = 0xD0
    BME280_RESET = 0xE0

    MEASURE_HUMI_CONFIG = 0xF2
    MEASURE_STATUS      = 0xF3
    MEASURE_MEAS_CONFIG = 0xF4

    GENERAL_CONFIG = 0xF5

    MEASURE_PRES_MSB  = 0xF7
    MEASURE_PRES_LSB  = 0xF8
    MEASURE_PRES_XLSB = 0xF9
    MEASURE_TEMP_MSB  = 0xFA
    MEASURE_TEMP_LSB  = 0xFB
    MEASURE_TEMP_XLSB = 0xFC
    MEASURE_HUMI_MSB  = 0xFD
    MEASURE_HUMI_LSB  = 0xFE

    HUMI_OVERSAMP_00   = 0b00000_000
    HUMI_OVERSAMP_01   = 0b00000_001
    HUMI_OVERSAMP_02   = 0b00000_010
    HUMI_OVERSAMP_04   = 0b00000_011
    HUMI_OVERSAMP_08   = 0b00000_100
    HUMI_OVERSAMP_16   = 0b00000_101
    HUMI_OVERSAMP_MASK = 0b00000_111

    PRES_OVERSAMP_00   = 0b000_000_00
    PRES_OVERSAMP_01   = 0b001_000_00
    PRES_OVERSAMP_02   = 0b010_000_00
    PRES_OVERSAMP_04   = 0b011_000_00
    PRES_OVERSAMP_08   = 0b100_000_00
    PRES_OVERSAMP_16   = 0b101_000_00
    PRES_OVERSAMP_MASK = 0b111_000_00

    TEMP_OVERSAMP_00   = 0b000_000_00
    TEMP_OVERSAMP_01   = 0b000_001_00
    TEMP_OVERSAMP_02   = 0b000_010_00
    TEMP_OVERSAMP_04   = 0b000_011_00
    TEMP_OVERSAMP_08   = 0b000_100_00
    TEMP_OVERSAMP_16   = 0b000_101_00
    TEMP_OVERSAMP_MASK = 0b000_111_00

    SENSOR_MODE_SLEEP  = 0b000_000_00
    SENSOR_MODE_FORCED = 0b000_000_01 
    SENSOR_MODE_NORMAL = 0b000_000_11

    # only in normal mode
    STANDBY_DURATION_0000_5 = 0b000_000_0_0 # 0.5 ms
    STANDBY_DURATION_0062_5 = 0b001_000_0_0 # 62.5 ms
    STANDBY_DURATION_0125_0 = 0b010_000_0_0 # 125 ms
    STANDBY_DURATION_0250_0 = 0b011_000_0_0 # 250 ms
    STANDBY_DURATION_0500_0 = 0b100_000_0_0 # 500 ms
    STANDBY_DURATION_1000_0 = 0b101_000_0_0 # 1000 ms
    STANDBY_DURATION_0010_0 = 0b110_000_0_0 # 10 ms
    STANDBY_DURATION_0020_0 = 0b111_000_0_0 # 20 ms

    IIR_TIME_CONST_OFF  = 0b000_000_0_0
    IIR_TIME_CONST_02   = 0b000_001_0_0
    IIR_TIME_CONST_04   = 0b000_010_0_0
    IIR_TIME_CONST_08   = 0b000_011_0_0
    IIR_TIME_CONST_16   = 0b000_100_0_0
    IIR_TIME_CONST_MASK = 0b000_111_0_0 

    SPI_3_WIRE_OFF = 0b000_000_0_0
    SPI_3_WIRE_ON  = 0b000_000_0_1

    def __init__(self, scl, sda):
        self.scl = scl
        self.sda = sda
        self.i2c = M.SoftI2C(scl=self.scl, sda=self.sda)
        
        self.failure = False
        addresses = self.i2c.scan()
        for address in addresses:
            if address in (self.SLAVE_ADDR_LOW, self.SLAVE_ADDR_HIGH):
                self.SLAVE_ADDR = address
                self.SLAVE_ADDR_WRITE =  (self.SLAVE_ADDR << 1)
                self.SLAVE_ADDR_READ  = ((self.SLAVE_ADDR << 1) | 0x01)
                break
            
        if self.SLAVE_ADDR == 0x00:
            self.failure = True
            raise RuntimeError("No devices on the I2C bus is a BMX280")

        self.t_fine = 0
        self.comp = self.get_compensations()

    def write_to_register(self, register, data):
        self.i2c.start()
        
        ack_addr_write = self.i2c.writeto(self.SLAVE_ADDR, bytes([self.SLAVE_ADDR_WRITE]))
        if (ack_addr_write == 1):
            self.i2c.writeto(self.SLAVE_ADDR, bytes([register, data]))
            
    def read_from_register(self, register, size):
        self.i2c.start()
        
        acks_addr_write = self.i2c.writeto(self.SLAVE_ADDR, bytes([self.SLAVE_ADDR_WRITE, register]))
        if (acks_addr_write == 2):
            self.i2c.start()
            acks_addr_read = self.i2c.writeto(self.SLAVE_ADDR, bytes([self.SLAVE_ADDR_READ]))
            if (acks_addr_read == 1):
                data = bytearray(size)
                self.i2c.readfrom_mem_into(self.SLAVE_ADDR, register, data)
                return data
            
        return None

    def reset(self):
        self.write_to_register(self.BME280_RESET, 0xB6)

    def get_id(self):
        return U.be_bytes_to_int(self.read_from_register(self.BME280_ID, 1))

    def configure_measure(self, meas_conf, humi_conf):
        self.write_to_register(self.MEASURE_HUMI_CONFIG, humi_conf)
        self.write_to_register(self.MEASURE_MEAS_CONFIG, meas_conf)

    def configure_general(self, general_conf):
        self.write_to_register(self.GENERAL_CONFIG, general_conf)

    def get_compensations(self):
        self.dig_t1 = self.read_from_register(0x88, 2)
        self.dig_t1 = U.le_bytes_to_int(self.dig_t1)
        
        self.dig_t2 = self.read_from_register(0x8A, 2)
        self.dig_t2 = U.le_bytes_to_int(self.dig_t2)
        self.dig_t2 = U.to_signed(self.dig_t2, 16)
        
        self.dig_t3 = self.read_from_register(0x8C, 2)
        self.dig_t3 = U.le_bytes_to_int(self.dig_t3)
        self.dig_t3 = U.to_signed(self.dig_t3, 16)
        
        self.dig_p1 = self.read_from_register(0x8E, 2)
        self.dig_p1 = U.le_bytes_to_int(self.dig_p1)
        
        self.dig_p2 = self.read_from_register(0x90, 2)
        self.dig_p2 = U.le_bytes_to_int(self.dig_p2)
        self.dig_p2 = U.to_signed(self.dig_p2, 16)
        
        self.dig_p3 = self.read_from_register(0x92, 2)
        self.dig_p3 = U.le_bytes_to_int(self.dig_p3)
        self.dig_p3 = U.to_signed(self.dig_p3, 16)
        
        self.dig_p4 = self.read_from_register(0x94, 2)
        self.dig_p4 = U.le_bytes_to_int(self.dig_p4)
        self.dig_p4 = U.to_signed(self.dig_p4, 16)
        
        self.dig_p5 = self.read_from_register(0x96, 2)
        self.dig_p5 = U.le_bytes_to_int(self.dig_p5)
        self.dig_p5 = U.to_signed(self.dig_p5, 16)
        
        self.dig_p6 = self.read_from_register(0x98, 2)
        self.dig_p6 = U.le_bytes_to_int(self.dig_p6)
        self.dig_p6 = U.to_signed(self.dig_p6, 16)
        
        self.dig_p7 = self.read_from_register(0x9A, 2)
        self.dig_p7 = U.le_bytes_to_int(self.dig_p7)
        self.dig_p7 = U.to_signed(self.dig_p7, 16)
        
        self.dig_p8 = self.read_from_register(0x9C, 2)
        self.dig_p8 = U.le_bytes_to_int(self.dig_p8)
        self.dig_p8 = U.to_signed(self.dig_p8, 16)
        
        self.dig_p9 = self.read_from_register(0x9E, 2)
        self.dig_p9 = U.le_bytes_to_int(self.dig_p9)
        self.dig_p9 = U.to_signed(self.dig_p9, 16)
        
        self.dig_h1 = self.read_from_register(0xA1, 1)
        self.dig_h1 = U.le_bytes_to_int(self.dig_h1)
        
        self.dig_h2 = self.read_from_register(0xE1, 2)
        self.dig_h2 = U.le_bytes_to_int(self.dig_h2)
        self.dig_h2 = U.to_signed(self.dig_h2, 16)
        
        self.dig_h3 = self.read_from_register(0xE3, 1)
        self.dig_h3 = U.le_bytes_to_int(self.dig_h3)
        
        self.dig_h4 = self.read_from_register(0xE4, 2)
        self.dig_h4 = U.be_bytes_to_int(self.dig_h4)
        self.dig_h4 = ((self.dig_h4 & 0xFF00) >> 4) | (self.dig_h4 & 0x000F)
        self.dig_h4 = U.to_signed(self.dig_h4, 16)
        
        self.dig_h5 = self.read_from_register(0xE5, 2)
        self.dig_h5 = U.le_bytes_to_int(self.dig_h5)
        self.dig_h5 = ((self.dig_h5 & 0xF000) >> 4) | (self.dig_h5 & 0x00FF)
        self.dig_h5 = U.to_signed(self.dig_h5, 16)
        
        self.dig_h6 = self.read_from_register(0xE7, 1)
        self.dig_h6 = U.le_bytes_to_int(self.dig_h6)
        self.dig_h6 = U.to_signed(self.dig_h6, 8)
        
        return {
            'dig_T1': self.dig_t1,
            'dig_T2': self.dig_t2,
            'dig_T3': self.dig_t3,
            'dig_P1': self.dig_p1,
            'dig_P2': self.dig_p2,
            'dig_P3': self.dig_p3,
            'dig_P4': self.dig_p4,
            'dig_P5': self.dig_p5,
            'dig_P6': self.dig_p6,
            'dig_P7': self.dig_p7,
            'dig_P8': self.dig_p8,
            'dig_P9': self.dig_p9,
            'dig_H1': self.dig_h1,
            'dig_H2': self.dig_h2,
            'dig_H3': self.dig_h3,
            'dig_H4': self.dig_h4,
            'dig_H5': self.dig_h5,
            'dig_H6': self.dig_h6
        }
    
    def compensate_temperature(self, raw):
        var1 = (((raw >> 3) - (U.to_signed(self.comp["dig_T1"], 32) << 1)) * U.to_signed(self.comp["dig_T2"], 32)) >> 11
        var2 = (((((raw >> 4) - U.to_signed(self.comp["dig_T1"], 32)) * ((raw >> 4) - U.to_signed(self.comp["dig_T1"], 32))) >> 12) * U.to_signed(self.comp["dig_T3"], 32)) >> 14
        self.t_fine = var1 + var2
        T = (self.t_fine * 5 + 128) >> 8
        return T / 100.0


    def compensate_pressure(self, raw):
        var1 = (self.t_fine >> 1) - 64000
        var2 = (((var1 >> 2) * (var1 >> 2)) >> 11) * U.to_signed(self.comp["dig_P6"], 32)
        var2 += ((var1 * U.to_signed(self.comp["dig_P5"], 32)) << 1)
        var2 = (var2 >> 2) + (U.to_signed(self.comp["dig_P4"], 32) << 16)
        var1 = (((self.comp["dig_P3"] * ((var1 >> 2) * (var1 >> 2)) >> 13) >> 3) + ((U.to_signed(self.comp["dig_P2"], 32) * var1) >> 1)) >> 18
        var1 = ((32768 + var1) * U.to_signed(self.comp["dig_P1"], 32)) >> 15

        if var1 == 0:
            return 0

        p = (((1048576 - raw) - (var2 >> 12)) * 3125)
        if p < 0x80000000:
            p = (p << 1) // var1
        else:
            p = (p // var1) * 2

        var1 = (U.to_signed(self.comp["dig_P9"], 16) * (((p >> 3) * (p >> 3)) >> 13)) >> 12
        var2 = ((p >> 2) * U.to_signed(self.comp["dig_P8"], 16)) >> 13
        p = p + ((var1 + var2 + U.to_signed(self.comp["dig_P7"], 16)) >> 4)

        return p / 100.0


    def compensate_humidity(self, raw):
        v_x1_u32r = self.t_fine - 76800
        v_x1_u32r = (((((raw << 14) - (U.to_signed(self.comp["dig_H4"], 16) << 20) - (U.to_signed(self.comp["dig_H5"], 16) * v_x1_u32r)) + 16384) >> 15) * (((((v_x1_u32r * U.to_signed(self.comp["dig_H6"], 16)) >> 10) * (((v_x1_u32r * U.to_signed(self.comp["dig_H3"], 16)) >> 11) + 32768)) >> 10) + 2097152) * U.to_signed(self.comp["dig_H2"], 16) + 8192) >> 14
        v_x1_u32r -= (((((v_x1_u32r >> 15) * (v_x1_u32r >> 15)) >> 7) * U.to_signed(self.comp["dig_H1"], 16)) >> 4)
        v_x1_u32r = 0 if v_x1_u32r < 0 else v_x1_u32r
        v_x1_u32r = 419430400 if v_x1_u32r > 419430400 else v_x1_u32r
        return (v_x1_u32r >> 12) / 1024.0

    def get_compensated_measures(self):
        readings = self.read_from_register(self.MEASURE_PRES_MSB, 8)
        
        # print("PRES_MSB :", zfilled_byte(readings[0] << 12, 24))
        # print("PRES_LSB :", zfilled_byte(readings[1] <<  4, 24))
        # print("PRES_XLSB:", zfilled_byte(readings[2] >>  4, 24))
        # print("TEMP_MSB :", zfilled_byte(readings[3] << 12, 24))
        # print("TEMP_LSB :", zfilled_byte(readings[4] <<  4, 24))
        # print("TEMP_XLSB:", zfilled_byte(readings[5] >>  4, 24))
        # print("HUMI_MSB :", zfilled_byte(readings[6] <<  8, 16))
        # print("HUMI_LSB :", zfilled_byte(readings[7] <<  0, 16))
        
        temperature = self.compensate_temperature(((readings[3] << 12) | (readings[4] << 4) | (readings[5] >> 4)))
        pressure = self.compensate_pressure(((readings[0] << 12) | (readings[1] << 4) | (readings[2] >> 4)))
        humidity = self.compensate_humidity((readings[6] << 8) | (readings[7]))
        
        return {
            'pres': pressure,
            'temp': temperature,
            'humi': humidity
        }
    