import webrepl

import machine as M
import network as N
import utime   as T

sta = N.WLAN(N.WLAN.IF_STA)
sta.active(True)

def connect_to_wifi():
    print("Connecting to Wi-Fi.", end="")
    sta.connect("rpi-ap", "BruhYnov")
    while not sta.isconnected():
        T.sleep(0.75)
        print(".", end="")
    print(" Done")
    print(sta.ifconfig())
    return True

connected_pin = M.Pin(12)

connect_to_wifi()
connected_pin.value(1)

webrepl.start()

