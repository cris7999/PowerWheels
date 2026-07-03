#include <esp_now.h>
#include <WiFi.h>

typedef struct struct_message {
    int contador;
} struct_message;

struct_message datosRecibidos;

// NUEVA FUNCIÓN: Callback de recepción corregido para ESP32 v3.x
void OnDataRecv(const esp_now_recv_info_t *recv_info, const uint8_t *incomingData, int len) {
  // Desempaquetamos los datos recibidos
  memcpy(&datosRecibidos, incomingData, sizeof(datosRecibidos));
  
  // Imprimimos el resultado inmediatamente
  Serial.print("Mensaje recibido con éxito -> Número: ");
  Serial.println(datosRecibidos.contador);
}
 
void setup() {
  Serial.begin(115200);
  
  WiFi.mode(WIFI_STA);

  if (esp_now_init() != ESP_OK) {
    Serial.println("Error inicializando ESP-NOW");
    return;
  }
  
  // Registramos el callback de recepción actualizado
  esp_now_register_recv_cb(OnDataRecv);
  Serial.println("Receptor listo y escuchando en segundo plano...");
}
 
void loop() {
  // El loop se queda completamente libre. No hace falta hacer nada aquí.
}