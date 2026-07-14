#include <esp_now.h>
#include <WiFi.h>

// La estructura debe coincidir EXACTAMENTE con la del emisor
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

struct_message datosRecibidos;

// Callback de recepción
void OnDataRecv(const esp_now_recv_info_t *recv_info, const uint8_t *incomingData, int len) {
  memcpy(&datosRecibidos, incomingData, sizeof(datosRecibidos));
  
  Serial.println("\n--- NUEVA TELEMETRÍA RECIBIDA ---");
  
  if (datosRecibidos.temperatura == -999.0) {
    Serial.println("Temp. Motor: ERROR DE LECTURA");
  } else {
    Serial.print("Temp. Motor: "); Serial.print(datosRecibidos.temperatura); Serial.println(" °C");
  }

  if (datosRecibidos.gpsValido) {
    Serial.print("Coordenadas: "); Serial.print(datosRecibidos.latitud, 6); Serial.print(", "); Serial.println(datosRecibidos.longitud, 6);
    Serial.print("Velocidad:   "); Serial.print(datosRecibidos.velocidad); Serial.println(" km/h");
    Serial.print("Satélites:   "); Serial.println(datosRecibidos.satelites);
  } else {
    Serial.print("GPS: Sin señal válida ");
    if(datosRecibidos.satelites > 0) {
      Serial.print("(Detectando "); Serial.print(datosRecibidos.satelites); Serial.println(" sats)");
    } else {
      Serial.println();
    }
  }
  Serial.println("---------------------------------");
}

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error inicializando ESP-NOW");
    return;
  }
  
  esp_now_register_recv_cb(OnDataRecv);
}

void loop() {
  // El receptor solo espera eventos de llegada en OnDataRecv
}
