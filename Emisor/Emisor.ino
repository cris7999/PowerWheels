#include <esp_now.h>
#include <WiFi.h>

// DIRECCIÓN MAC DE TU RECEPTOR
uint8_t receiverAddress[] = {0x28, 0x05, 0xA5, 0x2D, 0x27, 0x38}; 

typedef struct struct_message {
    int contador;
} struct_message;

struct_message misDatos;
esp_now_peer_info_t peerInfo;

int numeroAEnviar = 0;

// Callback de envío para ESP32 v3.x
void OnDataSent(const wifi_tx_info_t *tx_info, esp_now_send_status_t status) {
  Serial.print("Número enviado [");
  Serial.print(numeroAEnviar - 1);
  Serial.print("] -> Estado en el aire: ");
  Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Entregado (Receptor escuchó)" : "Buscando receptor...");
}
 
void setup() {
  Serial.begin(115200);
 
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
}
 
void loop() {
  misDatos.contador = numeroAEnviar;

  // Envía el mensaje (no bloquea el código si falla)
  esp_now_send(receiverAddress, (uint8_t *) &misDatos, sizeof(misDatos));
  
  numeroAEnviar++;
  delay(1000); // Emite estrictamente cada 1 segundo
}