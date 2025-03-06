import machine as M
import utime   as T
import utils   as U

from ucollections import OrderedDict

class OT722D66:
    MIN       = 1727  # around 0.1 cm deep
    LOW       = 2558 # around 1 cm deep
    MEDIUM    = 2947 # around 2 cm deep
    HIGH      = 3120 # around 3 cm deep
    MAX       = 3232 # around 4 cm deep

    def __init__(self, pin):
        self.pin = M.ADC(pin)

    # use only before installing the device
    def calibrate(self, pos_time, samp):
        values = OrderedDict({
            '0.1': 0,
            '0.5': 0,
            '1.0': 0,
            '1.5': 0,
            '2.0': 0,
            '2.5': 0,
            '3.0': 0,
            '3.5': 0,
            '4.0': 0
        })

        positionning_time = pos_time
        samples = samp
        for k in values.keys():
            print(f"Position the device on the {k} mark")
            T.sleep(positionning_time)
            print("Sampling...")
            print("Try no to move too much during the process")
            i = 0
            while i != samples:
                values[k] += wl_pin.read()
                i += 1
            values[k] /= samples
            
        print(values)

    def approximate_deepness(self, level):
        result = ((1.939899627123 * (10 ** (-9)) * (level ** 3))
                - (0.0000122748                  * (level ** 2))
                + (0.0265358                     * (level))
                - (19.1192))

        if result > 0 and result < 4:
            return result

        elif result < 0:
            return 0
        
        else:
            return 4
                        
    def convert_level_to_word(self, level):        
        integral = int(level)
        decimal = level - integral
        
        integral_bin = integral << 13
        decimal_bin = 0
        
        for i in range(1, 14):
            decimal_bin <<= 1
            if decimal >= (1 / (2 ** i)):
                #print(f"{decimal} is greater than {(1 / (2 ** i))}")
                decimal_bin |= 1
                decimal -= (1 / (2 ** i))
                
        #print("INTEGRAL:", zfilled_byte(integral_bin, 16))
        #print("DECIMAL :", zfilled_byte(decimal_bin, 16))
                
        return (integral_bin | decimal_bin)
                
    def get_raw_level(self):
        T.sleep(1)

        samples = 4000
        return (sum([self.pin.read() for i in range(samples)]) // samples)
                
    def get_level(self):        
        level = get_raw_level()
        return self.approximate_deepness(level)
        
def get_level_string(sensor, raw_level):
        if raw_level < sensor.MIN:
            return "EXTREMELY LOW"
        
        elif raw_level >= sensor.MIN and raw_level < sensor.LOW:
            return "VERY LOW"
            
        elif raw_level >= sensor.LOW and raw_level < sensor.MEDIUM:
            return "LOW"
        
        elif raw_level >= sensor.MEDIUM and raw_level < sensor.HIGH:
            return "MEDIUM"

        elif raw_level >= sensor.HIGH and raw_level < sensor.MAX:
            return "HIGH"
            
        else:
            return "VERY HIGH"
  