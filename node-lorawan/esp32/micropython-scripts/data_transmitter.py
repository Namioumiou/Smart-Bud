import machine      as M
import network      as N
import utime        as T
import umqtt.simple as MQTT
import esp          as E
import esp32        as E32

import utils        as U

import bme280
import bh1750
import ot722d66
import hw080

BROKER_IP_ADDRESS = "your_ip_address_here"

uplink_interval_seconds = 5 * 60 + 10

sta = N.WLAN(N.WLAN.IF_STA)
sta.active(True)

import gc
import os

def df():
  s = os.statvfs('//')
  return ('{0} MB'.format((s[0]*s[3])/1048576))

def free(full=False):
  F = gc.mem_free()
  A = gc.mem_alloc()
  T = F+A
  P = '{0:.2f}%'.format(F/T*100)
  if not full: return P
  else : return ('Total:{0} Free:{1} ({2})'.format(T,F,P))

def connect_to_wifi():
    print("Connecting to Wi-Fi.", end="")
    sta.connect("ssid", "mdp")
    while not sta.isconnected():
        T.sleep(0.75)
        print(".", end="")
    print(" Done")
    print(sta.ifconfig())

mqtt = MQTT.MQTTClient("esp32", BROKER_IP_ADDRESS, 1883, user="test_un1", password="test_pwd1")
def connect_to_mqtt_broker():
    #print("Connecting to MQTT broker")
    try:
        mqtt.connect()
        
    except MQTT.MQTTException as e:
        print("An MQTT error occured while trying to connect to the MQTT broker")
        print("Note: Check your connection parameters")
        print("Context:", e)
        M.reset()
        
    except Exception as e:
        print("An unknown error occured while trying to connect to the MQTT broker")
        print("Note: the connection most probably timed out")
        print("Context:", e)
        M.reset()

def init_bme280():
    th_sensor = None
    try:
        th_sensor = bme280.BMX280(M.Pin(25), M.Pin(26))

        th_sensor.reset()
        th_sensor.configure_measure(th_sensor.PRES_OVERSAMP_01 | th_sensor.TEMP_OVERSAMP_01 | th_sensor.SENSOR_MODE_FORCED, th_sensor.HUMI_OVERSAMP_01)
        th_sensor.configure_general(th_sensor.STANDBY_DURATION_1000_0 | th_sensor.IIR_TIME_CONST_OFF | th_sensor.SPI_3_WIRE_OFF)

    except Exception as e:
        th_sensor = None
        
    return th_sensor

def init_bh1750():
    l_sensor = None
    try:
        l_sensor = bh1750.BH1750(M.Pin(25), M.Pin(26))

    except Exception as e:
        l_sensor = None
    
    return l_sensor

MIN_WL_ACCEPT = 1672
MIN_SM_ACCEPT = 1000
MIN_SM_REASON = 1928

BMX280_TEMP_BIT = 0b00000001
BMX280_HUMI_BIT = 0b00000010
BH1750_BIT      = 0b00000100
OT722D66_BIT    = 0b00001000
HW080_BIT       = 0b00010000

th_sensor = init_bme280()
l_sensor  = init_bh1750()
wl_sensor = ot722d66.OT722D66(M.Pin(34))
sm_sensor = hw080.HW080(M.Pin(35))
pump      = M.Pin(14)

print("Ready")

print(df())
print(free(True))

while True:
    try:
        connect_to_wifi()
        connect_to_mqtt_broker()
        
        error_state = 0
        
        payload = bytearray(10)
        
        temperature = 0
        humidity = 0
        if th_sensor is not None:
            th_sensor.configure_measure(th_sensor.PRES_OVERSAMP_01 | th_sensor.TEMP_OVERSAMP_01 | th_sensor.SENSOR_MODE_FORCED, th_sensor.HUMI_OVERSAMP_01)
            temp_hum = th_sensor.get_compensated_measures()
            temperature = int(U.float_to_fixed_point(temp_hum['temp'], 7, 8), 2)
            
            if not th_sensor.is_bmp:
                humidity = int(U.float_to_fixed_point(temp_hum['humi'], 7, 8), 2)

            else:
                error_state = U.toggle_bit(error_state, BMX280_HUMI_BIT)

        else:
            error_state = U.toggle_bit(error_state, BMX280_TEMP_BIT | BMX280_HUMI_BIT)
            th_sensor = init_bme280()
                
        light = 0
        if l_sensor is not None:
            light = int(U.float_to_fixed_point(l_sensor.one_time_hrm2(), 15, 1), 2)
            
        else:
            error_state = error_state = U.toggle_bit(error_state, BH1750_BIT)
            l_sensor = init_bh1750()
            
        water_level = wl_sensor.get_raw_level()
        if water_level < MIN_WL_ACCEPT:
            error_state = error_state = U.toggle_bit(error_state, OT722D66_BIT)
            water_level = 0
        
        soil_moisture = sm_sensor.measure_analog()
        if soil_moisture < MIN_SM_ACCEPT:
            error_state = error_state = U.toggle_bit(error_state, HW080_BIT)
            soil_moisture = 0
            
        if soil_moisture < MIN_SM_REASON:
            pump.value(1)
        
        payload[0] = error_state
        
        payload[1:3] = temperature.to_bytes(2)
        payload[3:5] = humidity.to_bytes(2)
        payload[5:7] = light.to_bytes(2)
        payload[7:10] = ((water_level << 12) | (soil_moisture)).to_bytes(3)
        
        payload_str = "".join([hex(byte).replace("0x", "") if byte >= 0x10 else "0" + hex(byte).replace("0x", "") for byte in payload])
        
        print(payload_str)
        
        #print(f"Sending '{payload}' to MQTT broker on topic 'sensor_data'...")
        mqtt.publish(b"sensor_data", payload)
        
        print("Published")
        
        mqtt.disconnect()
        sta.disconnect()
        
        T.sleep(uplink_interval_seconds)

    except OSError as e:
        if "ECONNABORTED" in str(e):
            print(f"Connection lost. Attempting to reconnect.")
            connect_to_wifi()
            connect_to_mqtt_broker()

mqtt.disconnect()
sta.disconnect()
        
M.reset()