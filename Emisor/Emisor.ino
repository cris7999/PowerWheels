#include <esp_now.h>
#include <WiFi.h>
#include <TinyGPS++.h>
#include <max6675.h>

// --- DIRECCIÓN MAC DE TU RECEPTOR ---
uint8_t receiverAddress[] = {0x28, 0x05, 0xA5, 0x2D, 0x27, 0x38}; 

// --- CONFIGURACIÓN DE PINES ---
#define RXD2 16
#define TXD2 17

#define MAX6675_SO  13
#define MAX6675_CS  12
#define MAX6675_SCK 14

// --- INICIALIZACIÓN DE OBJETOS ---
TinyGPSPlus gps;
MAX6675 thermocouple(MAX6675_SCK, MAX6675_CS, MAX6675_SO);

// --- ESTRUCTURA DE DATOS (Telemetría) ---
// NOTA: Esta misma estructura exacta debe estar definida en el receptor.
typedef struct struct_message {
  float latitud;
  float longitud;
  float altitud;
  float velocidad;
  float temperatura;
  uint8_t satelites;
  uint8_t hora;
  uint8_t minuto;
  uint8_t segundo;
  bool gpsValido;
} struct_message;

struct_message telemetria;
esp_now_peer_info_t peerInfo;

unsigned long tiempoAnterior = 0;

// Callback de envío para ESP32 v3.x
void OnDataSent(const wifi_tx_info_t *tx_info, esp_now_send_status_t status) {
  Serial.print("Paquete de telemetría enviado -> Estado: ");
  Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Entregado con éxito" : "Fallo en la entrega");
}
 
void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, RXD2, TXD2);
 
  WiFi.mode(WIFI_STA);

  if (esp_now_init() != ESP_OK) {
    Serial.println("Error inicializando ESP-NOW");
    return;
  }

  esp_now_register_send_cb(OnDataSent);
  
  memcpy(peerInfo.peer_addr, receiverAddress, 6);
  peerInfo.channel = 0;  
  peerInfo.encrypt = false;
  
  if (esp_now_add_peer(&peerInfo) != ESP_OK){
    Serial.println("Fallo al añadir al receptor");
    return;
  }

  Serial.println("Transmisor Iniciado. Leyendo sensores...");
}
 
void loop() {
  // 1. Alimenta el parser del GPS constantemente
  while (Serial2.available() > 0) {
    gps.encode(Serial2.read());
  }

  // 2. Transmite los datos estrictamente cada 1 segundo (1000 ms)
  // Reemplazamos el delay() para que el bucle siga leyendo el GPS de fondo sin perder paquetes de datos
  if (millis() - tiempoAnterior >= 1000) {
    tiempoAnterior = millis();

    // Lectura de temperatura del motor
    float tempMotor = thermocouple.readCelsius();
    telemetria.temperatura = isnan(tempMotor) ? -999.0 : tempMotor; // -999.0 indicará error en el receptor

    // Lectura del GPS
    if (gps.location.isValid()) {
      telemetria.gpsValido = true;
      telemetria.latitud = gps.location.lat();
      telemetria.longitud = gps.location.lng();
      telemetria.altitud = gps.altitude.meters();
      
      // Filtro para ruido de velocidad quieto
      double vel = gps.speed.kmph();
      telemetria.velocidad = (vel < 1.5) ? 0.0 : vel;
      
      telemetria.satelites = gps.satellites.value();
      telemetria.hora = gps.time.hour();
      telemetria.minuto = gps.time.minute();
      telemetria.segundo = gps.time.second();
    } else {
      telemetria.gpsValido = false;
      telemetria.latitud = 0.0;
      telemetria.longitud = 0.0;
      telemetria.altitud = 0.0;
      telemetria.velocidad = 0.0;
      telemetria.satelites = gps.satellites.value(); // Puede tener satélites detectados pero no fijados todavía
    }

    // Envío del paquete por ESP-NOW
    esp_now_send(receiverAddress, (uint8_t *) &telemetria, sizeof(telemetria));
  }
}
