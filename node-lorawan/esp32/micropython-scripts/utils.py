def le_bytes_to_int(byte_string):
    result = ""
    for byte in bytes(reversed(byte_string)):
        result += hex(byte).replace("0x", "")
    return int(result, 16)

def be_bytes_to_int(byte_string):
    result = ""
    for byte in byte_string:
        result += hex(byte).replace("0x", "")
    return int(result, 16)

def to_signed(value, bitwidth):
    if value >= 2 ** (bitwidth - 1):
        return (-1) * ((2 ** bitwidth) - value)
    else:
        return value
    
def zfilled_byte(byte, length = 8):
    byte = bin(byte).replace("0b", "")
    
    if length <= 0 or len(byte) > length:
        raise RuntimeError("Invalid byte width")
    
    while len(byte) != length:
        byte = "0" + byte
        
    return byte

def float_from_fixed_point(binary: int, int_bit_count: int, dec_bit_count: int, signed: bool = True):
    result = 0.0

    negative = signed and (binary >> (int_bit_count + dec_bit_count))
    integral = (binary >> dec_bit_count) & ((2 ** int_bit_count) - 1)
    decimal = binary & ((2 ** dec_bit_count) - 1)

    result += integral
    for i in range(1, dec_bit_count + 1):
        if (decimal >> (dec_bit_count - i)) & 1:
            result += 1 / (2 ** (i))
            
    return result * ((-1) if negative else (1))

def float_to_fixed_point(value: float, int_bit_count: int, dec_bit_count: int):
    result = ""
    negative = value < 0
    result += "1" if negative else "0"

    integral = abs(int(value))
    decimal = abs(value) - integral
    result += zfilled_byte(int(bin(integral).replace("0b", ""), 2), int_bit_count)

    for i in range(1, dec_bit_count + 1):
        if decimal >= (1 / (2 ** i)):
            result += "1"
            decimal -= (1 / (2 ** i))
        else:
            result += "0"
    return result

def toggle_bit(value, bit):
    return value ^ (0x00 | (2 ** bit))
