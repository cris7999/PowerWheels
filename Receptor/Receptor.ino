#include <esp_now.h>
#include <WiFi.h>

// --- CONTROL DE FORMATO DE SALIDA ---
// true  -> Imprime JSON de una sola línea (Para tu Dashboard / Python)
// false -> Imprime texto legible clásico (Para depuración humana en Arduino IDE)
#define FORMATO_JSON true 

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

struct_message datosRecibidos;

// Callback de recepción corregido para ESP32 v3.x
void OnDataRecv(const esp_now_recv_info_t *recv_info, const uint8_t *incomingData, int len) {
  // Desempaquetamos los datos en nuestra estructura
  memcpy(&datosRecibidos, incomingData, sizeof(datosRecibidos));
  
  if (FORMATO_JSON) {
    // --- MODO DASHBOARD: Enviamos un JSON limpio en una sola línea (\n al final) ---
    Serial.print("{\"lat\":"); Serial.print(datosRecibidos.latitud, 6);
    Serial.print(",\"lng\":"); Serial.print(datosRecibidos.longitud, 6);
    Serial.print(",\"alt\":"); Serial.print(datosRecibidos.altitud, 1);
    Serial.print(",\"vel\":"); Serial.print(datosRecibidos.velocidad, 1);
    Serial.print(",\"temp\":"); Serial.print(datosRecibidos.temperatura, 1);
    Serial.print(",\"sat\":"); Serial.print(datosRecibidos.satelites);
    Serial.print(",\"gps\":"); Serial.print(datosRecibidos.gpsValido ? "true" : "false");
    Serial.println("}"); // El serial.println inserta el '\n' necesario para el readline() de Python
  } 
  else {
    // --- MODO DEPURACIÓN: Texto de fácil lectura para ti ---
    Serial.println("\n==========================================");
    Serial.println("         NUEVA TELEMETRÍA RECIBIDA        ");
    Serial.println("==========================================");
    
    Serial.print("Temp. Motor: ");
    if (datosRecibidos.temperatura == -999.0) {
      Serial.println("ERROR LECTURA (MAX6675)");
    } else {
      Serial.print(datosRecibidos.temperatura, 1);
      Serial.println(" °C");
    }
    Serial.println("------------------------------------------");

    if (datosRecibidos.gpsValido) {
      Serial.print("Latitud:     "); Serial.println(datosRecibidos.latitud, 6);
      Serial.print("Longitud:    "); Serial.println(datosRecibidos.longitud, 6);
      Serial.print("Altitud:     "); Serial.print(datosRecibidos.altitud, 1); Serial.println(" m");
      Serial.print("Velocidad:   "); Serial.print(datosRecibidos.velocidad, 1); Serial.println(" km/h");
      Serial.print("Satélites:   "); Serial.println(datosRecibidos.satelites);
      
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
}
 
void setup() {
  Serial.begin(115200);
  
  WiFi.mode(WIFI_STA);

  if (esp_now_init() != ESP_OK) {
    if (!FORMATO_JSON) Serial.println("Error inicializando ESP-NOW");
    return;
  }
  
  esp_now_register_recv_cb(OnDataRecv);
  if (!FORMATO_JSON) {
    Serial.println("Receptor listo y escuchando telemetría...");
  }
}
 
void loop() {
  // Se queda libre y ligero para dar máxima prioridad a la interrupción de recepción de ESP-NOW
}
