# Smart-Bud
Bienvenue dans notre solution tout-en-un pour un jardinage à la maison simple et à la portée de tous afin que chacun puisse disposer d'herbes fraiches à utiliser en cuisine sans avoir à s'embêter avec l'entretien des plantes. Smart Bud est en somme une serre miniature entièrement équipée pour surveiller et automatiser le processus qui permettra à vos herbes de pousser et de s'épanouir.

## Equipement
Smart Bud est équipé d'un capteur d'humidité et de température, ainsi que d'un capteur d'humidité du sol connecté avec une pompe et un système d'irrigation. Le produit est aussi équipé d'un capteur d'ultrasons qui permet de déterminer le niveau d'eau dans le réservoir. Une LED indique à l'utilisateur quand celui-ci est trop bas, afin qu'il le remplisse.

- 1 Breadboard
- 1 Arduino
- 1 Capteur d'ultrasons
- 1 Capteur d'humidité et de température (DHT11 pour nous)
- 1 Résistance 220Ω
- 1 LED
- 11 Câbles mâle/mâle
- 1 Câble USB/USB-B

## Initialisation
Le code a été réalisé avec Arduino IDE et tester avec Wokwi.

- Après avoir téléchargé le fichier "DebutCircuit.ino", il vous faudra installer la bibliothèque "DHT Sensor Library" d'Adafruit
- Faites ensuite les branchements nécessaire (image : InstallationIRLV1)
- Connectez l'Arduino à votre PC
- Uploadez le code dans l'Arduino
- Bravo, le projet est lancé !! 🙂


!! Attention : Pour tester le code sur Wokwi, il n'y a pas de DHT11, mais uniquement des DHT22. Il faut modifier le #define à la ligne 11 !!
