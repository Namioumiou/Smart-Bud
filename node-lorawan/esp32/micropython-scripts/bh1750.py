import machine as M
import utime   as T
import utils   as U
import random  as R

class BH1750:
    SLAVE_ADDR = 0x00 # can be 0x23 or 0x5C
    
    SLAVE_ADDR_LOW  = 0x23 # 0b00100011
    SLAVE_ADDR_HIGH = 0x5C # 0b01011100
    
    SLAVE_ADDR_WRITE = 0x00
    SLAVE_ADDR_READ  = 0x00
    
    # commands. used by the helper methods already.
    OPCODE_POWER_DOWN      = 0b0000_0000
    OPCODE_POWER_ON        = 0b0000_0001
    OPCODE_RESET           = 0b0000_0111
    OPCOCE_CONTINUOUS_HRM  = 0b0001_0000
    OPCOCE_CONTINUOUS_HRM2 = 0b0001_0001
    OPCOCE_CONTINUOUS_LRM  = 0b0001_0011
    OPCODE_ONE_TIME_HRM    = 0b0010_0000
    OPCODE_ONE_TIME_HRM2   = 0b0010_0001
    OPCODE_ONE_TIME_LRM    = 0b0010_0011
    
    def __init__(self, scl, sda):
        self.scl = scl
        self.sda = sda
        self.i2c = M.SoftI2C(scl=self.scl, sda=self.sda)

        addresses = self.i2c.scan()
        for address in addresses:
            if address in (self.SLAVE_ADDR_LOW, self.SLAVE_ADDR_HIGH):
                self.SLAVE_ADDR = address
                self.SLAVE_ADDR_WRITE =  (self.SLAVE_ADDR << 1)
                self.SLAVE_ADDR_READ  = ((self.SLAVE_ADDR << 1) | 0x01)
                break
            
        if self.SLAVE_ADDR == 0x00:
            raise RuntimeError("No devices on the I2C bus is a BH1750")
        
    def write_to_device(self, opcode):
        self.i2c.start()
        
        ack_addr_write = self.i2c.writeto(self.SLAVE_ADDR, bytes([self.SLAVE_ADDR_WRITE]))
        if (ack_addr_write == 1):
            ack_opc_write = self.i2c.writeto(self.SLAVE_ADDR, bytes([opcode]))
            if (ack_opc_write == 1):
                # all good
                pass
            
    def read_from_device(self, size):
        self.i2c.start()
        
        acks_addr_write = self.i2c.writeto(self.SLAVE_ADDR, bytes([self.SLAVE_ADDR_WRITE]))
        if (acks_addr_write == 1):
            self.i2c.start()
            acks_addr_read = self.i2c.writeto(self.SLAVE_ADDR, bytes([self.SLAVE_ADDR_READ]))
            if (acks_addr_read == 1):
                data = bytearray(size)
                self.i2c.readfrom_into(self.SLAVE_ADDR, data)
                return data
            
        return None
    
    def power_down(self):
        self.write_to_device(bytes([self.OPCODE_POWER_DOWN]))
    
    def power_on(self):
        self.write_to_device(bytes([self.OPCODE_POWER_ON]))
        T.sleep_us(2)
        
    def continuous_hrm(self):
        raise NotImplementedError("Continuous H-Resolution Mode measurement has not been implemented yet")
        
    def continuous_hrm2(self):
        raise NotImplementedError("Continuous H-Resolution Mode 2 measurement has not been implemented yet")
    
    def continuous_lrm(self):
        raise NotImplementedError("Continuous L-Resolution Mode measurement has not been implemented yet")
    
    def measure(self, opcode):
        self.write_to_device(bytes([opcode]))
        T.sleep_ms(120 if opcode in (self.OPCODE_ONE_TIME_HRM, self.OPCODE_ONE_TIME_HRM2) else 16)
        data = U.be_bytes_to_int(self.read_from_device(2))
        #data = U.be_bytes_to_int(R.randint(0x0000, 0xFFFF).to_bytes(2))
        return data
    
    def one_time_hrm(self):
        self.power_on()
        data = self.measure(self.OPCODE_ONE_TIME_HRM)
        return data
    
    def one_time_hrm2(self):
        self.power_on()
        data = self.measure(self.OPCODE_ONE_TIME_HRM2)
        decimal = 0.5 if (data & 0x01) else 0
        integral = (data >> 1)
        return integral + decimal
    
    def one_time_lrm(self):
        self.power_on()
        data = self.measure(self.OPCODE_ONE_TIME_LRM) & 0xFFFC
        return (data)
        