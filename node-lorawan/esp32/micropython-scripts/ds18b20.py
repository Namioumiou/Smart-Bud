import machine as M
import utime as T

# Initialize the dataou pin for one-wire communication (using GPIO pin 12 in this example)
DQ = M.Pin(4, M.Pin.OPEN_DRAIN)

def send_reset_pulse():
    DQ.value(0)  # Start reset pulse
    T.sleep_us(480)  # Hold low for 480us
    DQ.value(1)  # Release line
    T.sleep_us(70)  # Wait for 60us before checking presence pulse
    
    presence = DQ.value()
    
    T.sleep_us(410)
    
    if presence == 0:
        #print("Presence pulse detected!")
        return True  # Device is present
    else:
        #print("No device present")
        return False
    
def send_bit(bit):
    DQ.value(0)        # Pull low to start the timeslot
    T.sleep_us(2)      # Short hold
    
    if bit:
        DQ.value(1)    # If sending 1, release early
        T.sleep_us(58) # Finish the 60µs timeslot
    else:
        T.sleep_us(60) # Hold low for full 60µs for a 0
        DQ.value(1)    # Release line
    
    T.sleep_us(1)      # Ensure line is released before next bit
    
def send_command(command):
    #print("Sending", hex(command))  # Print binary representation
    
    for i in range(8):
        send_bit(command & 0x01)  # Send LSB first
        command >>= 1

def read_bit():
    DQ.value(0)       # Pull low to start the read slot
    T.sleep_us(2)     # Small delay
    DQ.value(1)       # Release the bus
    T.sleep_us(8)     # Wait before reading
    bit = DQ.value()  # Read data line
    T.sleep_us(50)    # Complete the read slot
    return bit

def read_byte():
    result = 0
    #print("Read ", end="")
    for i in range(8):  # Read 8 bits
        bit = read_bit()
        #print(bit, end="")
        result |= (bit << i)  # Set the corresponding bit in the result byte
        T.sleep_us(15)
        
    #print()
    
    return result

def get_ds18b20_address():    
    send_command(0x33)  # Send the "Read ROM" command (0x33)

    # Read 8 bytes (64 bits) to get the ROM code (device address)
    address = []
    for i in range(8):
        address.append(read_byte())  # Read each byte of the address

    return address

def skip_rom_command():
    send_command(0xCC)

def send_convert():
    send_command(0x44)

def get_temperature(only_bytes = False):
    send_command(0xBE)
    
    scratchpad = []
    for i in range(8):
        scratchpad.append(read_byte())  # Read each byte of the address
            
    temperature_bin = ((scratchpad[1] << 8) | scratchpad[0])
    
    if only_bytes:
        return temperature_bin.to_bytes(2)
    
    sign = int((temperature_bin & 0xF800) >> 11 == 0x1F)
    integer_part = (temperature_bin & 0x07F0) >> 4
    decimal_part_bin = temperature_bin & 0x000F
    
    decimal_part = 0
    power = 2
    for i in range(4):
        if decimal_part_bin >> (3 - i):
            decimal_part += 1 / (2 * power)
            
        power *= 2
    
    return (integer_part + decimal_part) * ((-1) if sign else (1))

# Example usage:
send_reset_pulse()  # Send the reset pulse  
address = get_ds18b20_address()
print("DS18B20 Address: ", [hex(byte) for byte in address])

while True:
    T.sleep_us(240)

    send_reset_pulse()  # Send the reset pulse
    skip_rom_command()
    send_convert()

    while DQ.value() == 0:
        #print("Converting temperature...")
        continue
    
    #print("Done converting.")

    T.sleep_us(240)

    send_reset_pulse()  # Send the reset pulse
    skip_rom_command()

    print(get_temperature(), "°C")
    
    T.sleep(0.5)

# while True:
#   current = DQ.value()
#   DQ.value(not current)
#   
#   T.sleep(2)
# 
#   print(f"LED {'off' if DQ.value() == 1 else 'on'} (value = {DQ.value()})")
