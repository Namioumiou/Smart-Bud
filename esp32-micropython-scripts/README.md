# How to setup the ESP32 to measure data periodically using the given scripts

For this purpose, we're gonna use Thonny to transfer the scripts. You are free to use whatever tool fits you best to transfer the files.

**1.** Open Thonny ;  
**2.** Plug in the target ESP32 on one of your available USB ports ;  
**3.** Open each script on the editor ;  
**4.** For each script, press the key combination CTRL+SHIFT+S and chose "MicroPython device" ;  

Now, the ESP32 has all the device to make the measures from the sensors and publish to the MQTT topic on which the Raspberry is subscribed.

In order to allow the ESP32 to communicate through MQTT with the broker on the Raspberry Pi, it's necessary to change the IP adress so that the ESP can publish to it. To do so, on your Raspberry Pi, either use the `ifconfig` (normally by default in the distribution) or `ip a` (which may require you to install the `iproute2` package) to retrieve the address of the Raspberry Pi. Then, simply copy-paste it in place of the current value of BROKER_IP_ADDRESS constant (line 13) so that the ESP uses the correct address.

If you wish to use the device without a PC (which you probably do), open the `boot.py` script from the ESP32's flash memory and import the `data_transmitter.py` script in it.

```py
import data_transmitter
```

This will allow the ESP32 to immediately initialize and transmit data from the sensor to the MQTT client on the Raspberry without any other input.

In case you're trying to test the code, this will probably annoy you. So to disable it, first open the `boot.py` file, then comment out the import line.

If you're are stuck in a boot loop, simply click on the output console of Thonny, then press CTRL+C multiple times on your keyboard until the Python interpreter prompt shows up again. Now you can do the previous procedure to disable on boot execution. 