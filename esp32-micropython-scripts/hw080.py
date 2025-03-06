import machine as M
import utime   as T

class HW080:
    SM_MAX_ACCEPTABLE = 4095
    SM_MIN_ACCEPTABLE = 1150
    
    def __init__(self, pin_adc = None, pin_dac = None):
        if pin_adc is None and pin_dac is None:
            raise RuntimeError("An ADC pin or a DAC pin is necessary to use the HW080")
        
        self.pin_adc = pin_adc
        self.pin_dac = pin_dac
        
        self.adc = M.ADC(M.Pin(pin_adc)) if pin_adc is not None else None
        self.adc.atten(M.ADC.ATTN_11DB)
        
        self.dac = M.DAC(M.Pin(pin_dac)) if pin_dac is not None else None
    
    def measure_analog(self):
        if self.pin_adc is None:
            raise RuntimeError("Unable to get analog measurement without an active ADC pin")
        return self.adc.read()
    
    def measure_digital(self):
        return NotImplementedError("Digital measurement has not been implemented yet")
        
    def convert_to_rh_percents(self, meas):
        if meas < self.SM_MIN_ACCEPTABLE:
            return 100.0
        
        elif meas > self.SM_MAX_ACCEPTABLE:
            return 0.0
        
        else:
            return 100.0 * ((self.SM_MAX_ACCEPTABLE - meas) / (self.SM_MAX_ACCEPTABLE - self.SM_MIN_ACCEPTABLE))
        
hw080 = HW080(M.Pin(35))

while True:
    value = hw080.measure_analog()
    print(round(hw080.convert_to_rh_percents(value), 2), f"%RH ({value})")
    T.sleep(1)