#!/bin/bash

# smart-bud-lora executable building
echo "Creating executable for smart-bud-lora"
cd /opt/Smart-Bud/raspberry-services/smart-bud-lora/examples/NonArduino/Raspberry/
./build.sh
cd -
rm -drf build # for some reason, the buidling creates a directory where it's not supposed to, so, I just delete it

# smart-bud-mqtt executable building
echo "Creating executable for smart-bud-mqtt"
cd /opt/Smart-Bud/raspberry-services/smart-bud-mqtt/
g++ -Wall -Wextra -pedantic -pedantic-errors main.cpp -lsqlite3 -lmosquitto -o /usr/local/bin/payload_receiver
cd -

# moving services at the right location
echo "Moving services to the correct location"
cp /opt/Smart-Bud/raspberry-services/smart-bud-lora.service /etc/systemd/system/
cp /opt/Smart-Bud/raspberry-services/smart-bud-mqtt.service /etc/systemd/system/

# reloading daemons to take new ones into account
echo "Reloading daemons"
systemctl daemon-reload
systemctl status smart-bud-lora --no-block --no-pager
systemctl status smart-bud-mqtt --no-block --no-pager
