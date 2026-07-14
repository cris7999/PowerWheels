#include <esp_now.h>
#include <WiFi.h>
#include <TinyGPS++.h>

// --- DIRECCIÓN MAC DE TU RECEPTOR ---
uint8_t receiverAddress[] = {0x28, 0x05, 0xA5, 0x2D, 0x27, 0x38}; 

// --- CONFIGURACIÓN DE PINES (Tus pines actuales de éxito) ---
#define RXD2 17
#define TXD2 16

#define MAX6675_SO  13
#define MAX6675_CS  26
#define MAX6675_SCK 18  
                        // ¡OJO!: Asegúrate de que el pin físico coincide con lo que definas aquí.

// --- INICIALIZACIÓN DE OBJETOS ---
TinyGPSPlus gps;

// --- ESTRUCTURA DE DATOS (Telemetría) ---
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

// --- FUNCIÓN DE LECTURA DEL MAX6675 SIN LIBRERÍA (Altamente compatible) ---
float leerTemperaturaMAX6675() {
  digitalWrite(MAX6675_CS, LOW);
  delayMicroseconds(1);

  uint16_t datosCrudos = 0;
  for (int i = 0; i < 16; i++) {
    digitalWrite(MAX6675_SCK, HIGH);
    delayMicroseconds(1);
    datosCrudos = (datosCrudos << 1) | digitalRead(MAX6675_SO);
    digitalWrite(MAX6675_SCK, LOW);
    delayMicroseconds(1);
  }
  digitalWrite(MAX6675_CS, HIGH);

  // Si el Bit 2 es 1, la termocupla está suelta
  if (datosCrudos & 0x04) {
    return -999.0; // Código de error
  }

  // Desplazamos 3 bits a la derecha para quitar los bits de estado y calculamos
  return (datosCrudos >> 3) * 0.25;
}

// Callback de envío para ESP32 v3.x
void OnDataSent(const wifi_tx_info_t *tx_info, esp_now_send_status_t status) {
  Serial.print("Paquete de telemetría enviado -> Estado: ");
  Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Entregado con éxito" : "Fallo en la entrega");
}
 
void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, RXD2, TXD2);
 
  // Configuración de los pines del sensor
  pinMode(MAX6675_CS, OUTPUT);
  pinMode(MAX6675_SCK, OUTPUT);
  pinMode(MAX6675_SO, INPUT);
  digitalWrite(MAX6675_CS, HIGH);
  digitalWrite(MAX6675_SCK, LOW);

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
  if (millis() - tiempoAnterior >= 1000) {
    tiempoAnterior = millis();

    // Lectura de temperatura mediante nuestra función a prueba de fallos
    float tempMotor = leerTemperaturaMAX6675();
    telemetria.temperatura = tempMotor; 

    // Lectura del GPS
    if (gps.location.isValid()) {
      telemetria.gpsValido = true;
      telemetria.latitud = gps.location.lat();
      telemetria.longitud = gps.location.lng();
      telemetria.altitud = gps.altitude.meters();
      
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
      telemetria.satelites = gps.satellites.value(); 
    }

    // Mostramos lo que vamos a enviar por el monitor serie
    Serial.print("Enviando -> Temp: "); 
    if(telemetria.temperatura == -999.0) {
       Serial.print("ERROR TEMP");
    } else {
       Serial.print(telemetria.temperatura); Serial.print(" C");
    }
    Serial.print(" | GPS Válido: "); Serial.print(telemetria.gpsValido ? "SÍ" : "NO");
    Serial.print(" | Satélites: "); Serial.println(telemetria.satelites);

    // Envío del paquete por ESP-NOW
    esp_now_send(receiverAddress, (uint8_t *) &telemetria, sizeof(telemetria));
  }
}
