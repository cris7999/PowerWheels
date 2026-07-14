#include <esp_now.h>
#include <WiFi.h>

// --- ESTRUCTURA DE DATOS (Telemetría) ---
// NOTA: Esta estructura es EXACTAMENTE idéntica a la del emisor.
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

// Callback de recepción corregido para ESP32 v3.x
void OnDataRecv(const esp_now_recv_info_t *recv_info, const uint8_t *incomingData, int len) {
  // Desempaquetamos los datos recibidos en nuestra estructura
  memcpy(&datosRecibidos, incomingData, sizeof(datosRecibidos));
  
  // Imprimimos el resultado de manera ordenada en la terminal
  Serial.println("\n==========================================");
  Serial.println("       NUEVA TELEMETRÍA RECIBIDA          ");
  Serial.println("==========================================");
  
  // 1. Mostrar Temperatura del Motor
  Serial.print("Temp. Motor: ");
  if (datosRecibidos.temperatura == -999.0) {
    Serial.println("¡ERROR! (Revisa cableado del MAX6675)");
  } else {
    Serial.print(datosRecibidos.temperatura, 1);
    Serial.println(" °C");
  }
  Serial.println("------------------------------------------");

  // 2. Mostrar datos del GPS según su validez
  if (datosRecibidos.gpsValido) {
    Serial.print("Latitud:     "); Serial.println(datosRecibidos.latitud, 6);
    Serial.print("Longitud:    "); Serial.println(datosRecibidos.longitud, 6);
    Serial.print("Altitud:     "); Serial.print(datosRecibidos.altitud, 1); Serial.println(" m");
    Serial.print("Velocidad:   "); Serial.print(datosRecibidos.velocidad, 1); Serial.println(" km/h");
    Serial.print("Satélites:   "); Serial.println(datosRecibidos.satelites);
    
    // Formatear hora de manera bonita (ej: 09:05:02)
    Serial.print("Hora UTC:    ");
    if (datosRecibidos.hora < 10) Serial.print("0"); Serial.print(datosRecibidos.hora); Serial.print(":");
    if (datosRecibidos.minuto < 10) Serial.print("0"); Serial.print(datosRecibidos.minuto); Serial.print(":");
    if (datosRecibidos.segundo < 10) Serial.print("0"); Serial.println(datosRecibidos.segundo);
  } else {
    Serial.println("Estado GPS:  Buscando señal...");
    Serial.print("Satélites:   "); Serial.print(datosRecibidos.satelites);
    Serial.println(" (Insuficientes para posicionamiento)");
  }
  Serial.println("==========================================");
}
 
void setup() {
  Serial.begin(115200);
  
  // Configurar Wi-Fi en modo Estación (necesario para ESP-NOW)
  WiFi.mode(WIFI_STA);

  // Inicializar ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error inicializando ESP-NOW");
    return;
  }
  
  // Registrar el callback de recepción
  esp_now_register_recv_cb(OnDataRecv);
  Serial.println("Receptor listo y escuchando telemetría en segundo plano...");
}
 
void loop() {
  // El loop se queda completamente libre. 
  // Los datos se imprimen automáticamente en cuanto OnDataRecv se activa.
}
