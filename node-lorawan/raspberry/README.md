# 1.2 Comment mettre en place la Raspberry et le HAT SX1262 ?

## Install the necessary packages

`sudo apt install mosquitto mosquitto-client sqlite3 libsqlite3-dev`

## Clone the project

**1.** `cd /opt/`  
**2.** `sudo git clone https://github.com/Namioumiou/Smart-Bud`  

## Build services using the script

**1.** `cd Smart-Bud/raspberry-services/`  
**2.** `sudo ./setup.sh`

The servics are now running in the background and sending data every 20 minutes to The Things Network.