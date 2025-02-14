#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <DHT_U.h>

// Définition des pins
#define ECHO_PIN 2
#define TRIG_PIN 3
#define DHTPIN 4
#define LED_PIN 13

#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  Serial.println(F("Démarrage des capteurs..."));

  sensor_t sensor;
  dht.begin();

  
  pinMode(LED_PIN, OUTPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

}

float readDistanceCM() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  int duration = pulseIn(ECHO_PIN, HIGH);
  return duration * 0.034 / 2;
}

void loop() {
  unsigned long currentMillis = millis();
  static unsigned long lastDHTRead = 0;

  // Capteur ultrason
  float distance = readDistanceCM();
  bool isNearby = distance < 10;
  Serial.print("Distance mesurée: ");
  Serial.print(distance);
  Serial.println(" cm");

  if (isNearby) {
    digitalWrite(LED_PIN, HIGH);
  } else {
    digitalWrite(LED_PIN, LOW);
  }

  // DHT22 : mesure toutes les 250 ms minimum
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  // Vérifier si la lecture du capteur a échoué
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println(F("Erreur : Impossible de lire les données du DHT22 !"));
    return; 
  }

  // Afficher les valeurs sur le moniteur série
  Serial.print(F("Température : "));
  Serial.print(temperature);
  Serial.println(F(" °C"));

  Serial.print(F("Humidité : "));
  Serial.print(humidity);
  Serial.println(F(" %"));


  delay(500);
  }
