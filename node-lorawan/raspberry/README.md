# 1.2 Comment mettre en place la Raspberry et le HAT SX1262 ?

## Installez les packages nécessaires

`sudo apt install mosquitto mosquitto-client sqlite3 libsqlite3-dev`

## Clonez le projet

**1.** `cd /opt/`  
**2.** `sudo git clone https://github.com/Namioumiou/Smart-Bud`  

## Build les services en utilisant le script

**1.** `cd Smart-Bud/raspberry-services/`  
**2.** `sudo ./setup.sh`

Les services tournent maitenant en arrière-plan et envoie des données à The Things Network toute les 20 minutes.
