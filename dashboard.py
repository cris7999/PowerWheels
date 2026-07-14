import sys
import json
import csv
import time
from datetime import datetime
import threading
import serial
import serial.tools.list_ports
import customtkinter as ctk

# Configuración visual
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class TelemetryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("RACE CONTROL - TELEMETRÍA EN TIEMPO REAL")
        self.geometry("1000x600")
        
        # Variables de estado
        self.serial_port = None
        self.running = False
        self.csv_file = None
        self.csv_writer = None
        
        self.create_widgets()
        self.init_csv_logger()

    def init_csv_logger(self):
        # Crea un log CSV único basado en la marca de tiempo de la sesión
        filename = f"log_carrera_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.csv_file = open(filename, mode='w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        # Cabecera del log de telemetría
        self.csv_writer.writerow(["Timestamp", "Latitud", "Longitud", "Altitud", "Velocidad", "Temp_Motor", "Satélites", "GPS_Valido"])
        self.csv_file.flush()

    def create_widgets(self):
        # --- HEADER / CONFIGURACIÓN DE PUERTO ---
        self.header_frame = ctk.CTkFrame(self, height=60)
        self.header_frame.pack(fill="x", padx=20, pady=10)
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="RACE TELEMETRY SYSTEM", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(side="left", padx=20)

        # Selector de Puerto COM
        self.port_label = ctk.CTkLabel(self.header_frame, text="Puerto:")
        self.port_label.pack(side="left", padx=5)
        
        self.port_combobox = ctk.CTkComboBox(self.header_frame, values=self.get_serial_ports())
        self.port_combobox.pack(side="left", padx=5)
        
        self.connect_btn = ctk.CTkButton(self.header_frame, text="Conectar", command=self.toggle_connection, fg_color="green")
        self.connect_btn.pack(side="left", padx=20)

        # --- GRID DE DATOS ---
        self.grid_frame = ctk.CTkFrame(self)
        self.grid_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.grid_frame.columnconfigure((0, 1, 2), weight=1)
        self.grid_frame.rowconfigure((0, 1), weight=1)

        # 1. Temperatura Motor (Con alerta visual)
        self.temp_frame = ctk.CTkFrame(self.grid_frame, fg_color="#1e1e1e")
        self.temp_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.temp_title = ctk.CTkLabel(self.temp_frame, text="TEMP. MOTOR", font=ctk.CTkFont(size=14, weight="bold"))
        self.temp_title.pack(pady=10)
        self.temp_val = ctk.CTkLabel(self.temp_frame, text="0.0 °C", font=ctk.CTkFont(size=36, weight="bold"), text_color="#17a2b8")
        self.temp_val.pack(expand=True)

        # 2. Velocidad
        self.vel_frame = ctk.CTkFrame(self.grid_frame, fg_color="#1e1e1e")
        self.vel_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.vel_title = ctk.CTkLabel(self.vel_frame, text="VELOCIDAD", font=ctk.CTkFont(size=14, weight="bold"))
        self.vel_title.pack(pady=10)
        self.vel_val = ctk.CTkLabel(self.vel_frame, text="0.0 km/h", font=ctk.CTkFont(size=36, weight="bold"), text_color="#28a745")
        self.vel_val.pack(expand=True)

        # 3. Estado GPS
        self.gps_frame = ctk.CTkFrame(self.grid_frame, fg_color="#1e1e1e")
        self.gps_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        self.gps_title = ctk.CTkLabel(self.gps_frame, text="ESTADO GPS / SATÉLITES", font=ctk.CTkFont(size=14, weight="bold"))
        self.gps_title.pack(pady=10)
        self.gps_val = ctk.CTkLabel(self.gps_frame, text="SIN FIJAR (0 Sats)", font=ctk.CTkFont(size=24, weight="bold"), text_color="orange")
        self.gps_val.pack(expand=True)

        # 4. Latitud y Longitud
        self.coords_frame = ctk.CTkFrame(self.grid_frame, fg_color="#1e1e1e")
        self.coords_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.coords_title = ctk.CTkLabel(self.coords_frame, text="COORDENADAS DE POSICIÓN", font=ctk.CTkFont(size=14, weight="bold"))
        self.coords_title.pack(pady=10)
        self.coords_val = ctk.CTkLabel(self.coords_frame, text="Lat: --- | Lng: ---", font=ctk.CTkFont(size=20), text_color="#ffffff")
        self.coords_val.pack(expand=True)

        # 5. Altitud
        self.alt_frame = ctk.CTkFrame(self.grid_frame, fg_color="#1e1e1e")
        self.alt_frame.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")
        self.alt_title = ctk.CTkLabel(self.alt_frame, text="ALTITUD", font=ctk.CTkFont(size=14, weight="bold"))
        self.alt_title.pack(pady=10)
        self.alt_val = ctk.CTkLabel(self.alt_frame, text="0.0 m", font=ctk.CTkFont(size=24, weight="bold"))
        self.alt_val.pack(expand=True)

    def get_serial_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def toggle_connection(self):
        if not self.running:
            port = self.port_combobox.get()
            try:
                self.serial_port = serial.Serial(port, 115200, timeout=1)
                self.running = True
                self.connect_btn.configure(text="Desconectar", fg_color="red")
                # Iniciamos hilo de escucha para no colgar la UI
                self.thread = threading.Thread(target=self.listen_serial, daemon=True)
                self.thread.start()
            except Exception as e:
                print(f"Error de conexión: {e}")
        else:
            self.running = False
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            self.connect_btn.configure(text="Conectar", fg_color="green")

    def listen_serial(self):
        while self.running:
            try:
                if self.serial_port.in_waiting > 0:
                    line = self.serial_port.readline().decode('utf-8').strip()
                    self.process_packet(line)
            except Exception as e:
                print(f"Error leyendo puerto: {e}")
                break

    def process_packet(self, raw_data):
        try:
            data = json.loads(raw_data)
            
            # 1. Procesar Temperatura
            temp = data.get("temp", 0.0)
            if temp == -999.0:
                self.temp_val.configure(text="ERROR TERM.", text_color="red")
                self.temp_frame.configure(fg_color="#3a1111")
            else:
                self.temp_val.configure(text=f"{temp:.1f} °C")
                # Alerta crítica: Si pasa de 100°C pintamos el recuadro de rojo
                if temp > 100.0:
                    self.temp_frame.configure(fg_color="#3a1111") # Fondo rojo oscuro
                    self.temp_val.configure(text_color="red")
                else:
                    self.temp_frame.configure(fg_color="#1e1e1e")
                    self.temp_val.configure(text_color="#17a2b8")

            # 2. Velocidad
            vel = data.get("vel", 0.0)
            self.vel_val.configure(text=f"{vel:.1f} km/h")

            # 3. GPS / Satélites
            gps_valido = data.get("gps", False)
            sat = data.get("sat", 0)
            if gps_valido:
                self.gps_val.configure(text=f"FIJADO ({sat} Sats)", text_color="#28a745")
                self.coords_val.configure(text=f"Lat: {data.get('lat', 0.0):.6f} | Lng: {data.get('lng', 0.0):.6f}")
                self.alt_val.configure(text=f"{data.get('alt', 0.0):.1f} m")
            else:
                self.gps_val.configure(text=f"BUSCANDO ({sat} Sats)", text_color="orange")
                self.coords_val.configure(text="Lat: BUSCANDO | Lng: BUSCANDO")

            # 4. Escribir al log de respaldo
            self.csv_writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                data.get("lat"), data.get("lng"), data.get("alt"),
                data.get("vel"), temp, sat, gps_valido
            ])
            self.csv_file.flush()

        except json.JSONDecodeError:
            # Ignoramos líneas incompletas de arranque o de ruido
            pass

    def on_closing(self):
        self.running = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        if self.csv_file:
            self.csv_file.close()
        self.destroy()

if __name__ == "__main__":
    app = TelemetryApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()