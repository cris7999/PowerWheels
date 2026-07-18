import streamlit as st
import pandas as pd
import pydeck as pdk
import time
import math
import os
import base64
from PIL import Image, ImageDraw

# === 1. CONFIGURACIÓN DE LA PÁGINA ===
st.set_page_config(page_title="Telemetría + Récords", layout="wide", initial_sidebar_state="collapsed")
st.title("🏎️ Telemetría y Historial de Tiempos por Sector")

LAT_BASE = 43.2966
LNG_BASE = -7.3388

# Límites del recuadro del circuito real para la capa BitmapLayer
MIN_LNG = -7.3410
MAX_LNG = -7.3370
MIN_LAT = 43.2955
MAX_LAT = 43.2978

# Coordenadas reales del trazado del circuito PTC Escuela, A Pastoriza (Lugo)
PTC_POINTS = [
    {'lat': 43.2968702, 'lon': -7.3384242}, {'lat': 43.2973895, 'lon': -7.3400175}, {'lat': 43.2974129, 'lon': -7.3401328},
    {'lat': 43.2974012, 'lon': -7.3402508}, {'lat': 43.2973544, 'lon': -7.3403581}, {'lat': 43.2972763, 'lon': -7.3404359},
    {'lat': 43.2971748, 'lon': -7.3404708}, {'lat': 43.2967512, 'lon': -7.3405539}, {'lat': 43.2966672, 'lon': -7.3405432},
    {'lat': 43.2965969, 'lon': -7.3405083}, {'lat': 43.2965306, 'lon': -7.3404305}, {'lat': 43.2964798, 'lon': -7.3402937},
    {'lat': 43.2962963, 'lon': -7.3396259}, {'lat': 43.2962885, 'lon': -7.3395132}, {'lat': 43.2963275, 'lon': -7.3394247},
    {'lat': 43.2964251, 'lon': -7.3392852}, {'lat': 43.2965189, 'lon': -7.3391833}, {'lat': 43.2966067, 'lon': -7.3391726},
    {'lat': 43.2966594, 'lon': -7.3391967}, {'lat': 43.2967004, 'lon': -7.3392503}, {'lat': 43.296716, 'lon': -7.3393281},
    {'lat': 43.2967141, 'lon': -7.339422}, {'lat': 43.296677, 'lon': -7.3394891}, {'lat': 43.2966008, 'lon': -7.3395642},
    {'lat': 43.2965559, 'lon': -7.3396259}, {'lat': 43.2965345, 'lon': -7.339701}, {'lat': 43.2965384, 'lon': -7.3398404},
    {'lat': 43.296593, 'lon': -7.3400309}, {'lat': 43.2966633, 'lon': -7.3401838}, {'lat': 43.2967473, 'lon': -7.3402401},
    {'lat': 43.2968507, 'lon': -7.3402428}, {'lat': 43.2969893, 'lon': -7.3401998}, {'lat': 43.2970655, 'lon': -7.3401113},
    {'lat': 43.2970908, 'lon': -7.3399719}, {'lat': 43.2970889, 'lon': -7.3398807}, {'lat': 43.2970459, 'lon': -7.3397144},
    {'lat': 43.2968175, 'lon': -7.339025}, {'lat': 43.2967512, 'lon': -7.3389124}, {'lat': 43.2966809, 'lon': -7.3387971},
    {'lat': 43.2965755, 'lon': -7.3385262}, {'lat': 43.2964857, 'lon': -7.3383008}, {'lat': 43.296431, 'lon': -7.3382499},
    {'lat': 43.2963471, 'lon': -7.3382257}, {'lat': 43.2962787, 'lon': -7.3382713}, {'lat': 43.2962397, 'lon': -7.3383491},
    {'lat': 43.2962299, 'lon': -7.3384457}, {'lat': 43.2962553, 'lon': -7.3385557}, {'lat': 43.2963061, 'lon': -7.33862},
    {'lat': 43.2963607, 'lon': -7.3386656}, {'lat': 43.2964037, 'lon': -7.33873}, {'lat': 43.2964173, 'lon': -7.3388131},
    {'lat': 43.2964017, 'lon': -7.338907}, {'lat': 43.2963393, 'lon': -7.3389768}, {'lat': 43.2962787, 'lon': -7.3390089},
    {'lat': 43.2962007, 'lon': -7.3389902}, {'lat': 43.2961167, 'lon': -7.3388829}, {'lat': 43.2960718, 'lon': -7.3387461},
    {'lat': 43.2960347, 'lon': -7.3385074}, {'lat': 43.296025, 'lon': -7.3382177}, {'lat': 43.2960035, 'lon': -7.3380487},
    {'lat': 43.2959449, 'lon': -7.337861}, {'lat': 43.2958824, 'lon': -7.3377161}, {'lat': 43.2958551, 'lon': -7.3375874},
    {'lat': 43.2958746, 'lon': -7.3374533}, {'lat': 43.2959352, 'lon': -7.3373433}, {'lat': 43.2960308, 'lon': -7.337295},
    {'lat': 43.2961304, 'lon': -7.3373165}, {'lat': 43.2961928, 'lon': -7.3373835}, {'lat': 43.2962826, 'lon': -7.3375471},
    {'lat': 43.2963666, 'lon': -7.3377242}, {'lat': 43.2964564, 'lon': -7.3378636}, {'lat': 43.2965774, 'lon': -7.3379897},
    {'lat': 43.2966867, 'lon': -7.3381024}, {'lat': 43.2967765, 'lon': -7.3382204}, {'lat': 43.2968234, 'lon': -7.3383116},
    {'lat': 43.2968702, 'lon': -7.3384242}
]

# === GENERACIÓN DE LA IMAGEN DEL CIRCUITO REAL ===
def generar_circuito_png(filename="circuit_ptc.png"):
    img_size = 1000

    def latlng_to_pixel(lat, lng):
        x = int((lng - MIN_LNG) / (MAX_LNG - MIN_LNG) * img_size)
        y = int((1.0 - (lat - MIN_LAT) / (MAX_LAT - MIN_LAT)) * img_size)
        return x, y

    # Convertir todos los puntos a coordenadas de píxeles
    points = [latlng_to_pixel(pt['lat'], pt['lon']) for pt in PTC_POINTS]
    steps = len(points) - 1

    img = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Capa 1: Bordillo externo de seguridad (rojo y blanco)
    curb_width = 36
    for i in range(steps):
        p1 = points[i]
        p2 = points[i+1]
        color = (255, 75, 75, 255) if (i // 3) % 2 == 0 else (255, 255, 255, 255)
        draw.line([p1, p2], fill=color, width=curb_width, joint="round")

    # Capa 2: Pista de Asfalto (gris oscuro)
    asphalt_width = 30
    asphalt_color = (30, 35, 45, 255)
    draw.line(points, fill=asphalt_color, width=asphalt_width, joint="round")

    # Capa 3: Línea central discontinua
    centerline_color = (150, 160, 180, 200)
    for i in range(0, steps, 2):
        p1 = points[i]
        p2 = points[min(i+1, steps)]
        draw.line([p1, p2], fill=centerline_color, width=2, joint="round")

    # Capa 4: Línea de Meta (Damero / Ajedrezado)
    meta_pixel = points[0]
    p_before = points[-2]
    p_after = points[1]
    dx = p_after[0] - p_before[0]
    dy = p_after[1] - p_before[1]
    length = math.sqrt(dx*dx + dy*dy)
    if length > 0:
        nx = -dy / length
        ny = dx / length
        half_width = 22
        line_start = (int(meta_pixel[0] - nx * half_width), int(meta_pixel[1] - ny * half_width))
        line_end = (int(meta_pixel[0] + nx * half_width), int(meta_pixel[1] + ny * half_width))
        draw.line([line_start, line_end], fill=(255, 255, 255, 255), width=6)
        draw.line([line_start, line_end], fill=(0, 0, 0, 255), width=6, joint="round")
        
        for offset in range(-half_width, half_width, 6):
            cx = int(meta_pixel[0] + nx * offset)
            cy = int(meta_pixel[1] + ny * offset)
            color = (255, 255, 255, 255) if (offset // 6) % 2 == 0 else (0, 0, 0, 255)
            draw.rectangle([cx-3, cy-3, cx+3, cy+3], fill=color)

    img.save(filename, "PNG")

@st.cache_data
def get_circuit_image_base64(filename="circuit_ptc.png"):
    if not os.path.exists(filename):
        generar_circuito_png(filename)
    try:
        with open(filename, "rb") as f:
            data = f.read()
            return f'"data:image/png;base64,{base64.b64encode(data).decode()}"'
    except Exception:
        return '""'

# === 2. CONFIGURACIÓN DEL CIRCUITO ===
SECTORES = [
    {"id": "Sector 1", "lat": 43.2965345, "lng": -7.339701},
    {"id": "Sector 2", "lat": 43.2964173, "lng": -7.3388131},
    {"id": "Meta",     "lat": 43.2968702, "lng": -7.3384242}
]
RADIO_DETECCION_METROS = 20.0

# === 3. INICIALIZACIÓN DE LA MEMORIA ===
if "route_index" not in st.session_state:
    st.session_state.route_index = 0.0
if "sector_idx" not in st.session_state:
    st.session_state.sector_idx = 0
if "t_ultimo_sector" not in st.session_state:
    st.session_state.t_ultimo_sector = time.time()
if "tiempos_vuelta" not in st.session_state:
    st.session_state.tiempos_vuelta = {}
if "historial_ruta" not in st.session_state:
    st.session_state.historial_ruta = []
if "telemetria" not in st.session_state:
    st.session_state.telemetria = {"lat": LAT_BASE, "lng": LNG_BASE, "vel": 0.0, "temp": 85.0}

# ESTRUCTURA PARA EL HISTORIAL DE RÉCORDS (Último tiempo y Top 3)
if "records_sectores" not in st.session_state:
    st.session_state.records_sectores = {
        "Sector 1": {"ultimo": "-", "top3": []},
        "Sector 2": {"ultimo": "-", "top3": []},
        "Meta":     {"ultimo": "-", "top3": []}
    }
if "vuelta_completa_flag" not in st.session_state:
    st.session_state.vuelta_completa_flag = False
if "ultimo_total_vuelta" not in st.session_state:
    st.session_state.ultimo_total_vuelta = "-"

# === 4. FÓRMULA DE HAVERSINE ===
def calcular_distancia(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    return R * (2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a)))

# === 5. SIMULACIÓN ===
# Ángulo virtual calculado para emular curvas y rectas con fines estéticos en telemetría
ang_virtual = (st.session_state.route_index / len(PTC_POINTS)) * 2 * math.pi
es_recta = math.cos(ang_virtual * 2) > 0

sim_vel = round(110.0 + 30.0 * math.sin(ang_virtual * 3) if es_recta else 60.0 + 15.0 * math.cos(ang_virtual), 1)
sim_temp = round(85.0 + (sim_vel / 10.0) + (math.sin(ang_virtual) * 2), 1)

# Incrementar posición a lo largo de la pista real basada en la velocidad
vel_ms = sim_vel / 3.6
dist_step = vel_ms * 0.1  # Actualización cada 0.1s
idx_step = dist_step / 15.8  # Distancia promedio de 15.8m entre puntos
st.session_state.route_index += idx_step

if st.session_state.route_index >= len(PTC_POINTS):
    st.session_state.route_index -= len(PTC_POINTS)

# Interpolar posición actual en coordenadas reales
i1 = int(st.session_state.route_index) % len(PTC_POINTS)
i2 = (i1 + 1) % len(PTC_POINTS)
t_ratio = st.session_state.route_index - int(st.session_state.route_index)

sim_lat = PTC_POINTS[i1]['lat'] * (1 - t_ratio) + PTC_POINTS[i2]['lat'] * t_ratio
sim_lng = PTC_POINTS[i1]['lon'] * (1 - t_ratio) + PTC_POINTS[i2]['lon'] * t_ratio

st.session_state.telemetria = {"lat": sim_lat, "lng": sim_lng, "vel": sim_vel, "temp": sim_temp}
st.session_state.historial_ruta.append({"lat": sim_lat, "lng": sim_lng})

if len(st.session_state.historial_ruta) > 100:
    st.session_state.historial_ruta.pop(0)

# === LÓGICA DE CRONOMETRAJE ACTUALIZADA ===
obj = SECTORES[st.session_state.sector_idx]
dist = calcular_distancia(sim_lat, sim_lng, obj["lat"], obj["lng"])

if dist <= RADIO_DETECCION_METROS:
    ahora = time.time()
    t_sector = round(ahora - st.session_state.t_ultimo_sector, 3)
    
    # 1. Guardar último tiempo del sector actual
    st.session_state.records_sectores[obj["id"]]["ultimo"] = t_sector
    
    # 2. Añadir al Top 3, ordenar de menor a mayor y quedarse con los 3 mejores
    st.session_state.records_sectores[obj["id"]]["top3"].append(t_sector)
    st.session_state.records_sectores[obj["id"]]["top3"] = sorted(st.session_state.records_sectores[obj["id"]]["top3"])[:3]
    
    st.session_state.tiempos_vuelta[obj["id"]] = t_sector
    st.session_state.vuelta_completa_flag = False
    
    if obj["id"] == "Meta":
        st.session_state.ultimo_total_vuelta = round(sum(st.session_state.tiempos_vuelta.values()), 3)
        st.session_state.vuelta_completa_flag = True
        st.session_state.tiempos_vuelta.clear()
        st.session_state.sector_idx = 0
    else:
        st.session_state.sector_idx += 1
    
    st.session_state.t_ultimo_sector = ahora

# === 6. DISEÑO DE LA INTERFAZ GRÁFICA ===
col_mapa, col_datos = st.columns([2, 1])

with col_mapa:
    st.subheader("📍 Trazada en el Circuito Virtual")
    
    df_coche = pd.DataFrame([st.session_state.telemetria])
    df_ruta = pd.DataFrame(st.session_state.historial_ruta)
    df_sectores = pd.DataFrame(SECTORES)

    capa_coche = pdk.Layer(
        "ScatterplotLayer", df_coche,
        get_position=["lng", "lat"], get_color=[255, 75, 75, 250], get_radius=8,
    )
    capa_ruta = pdk.Layer(
        "PathLayer", df_ruta, width_min_pixels=4,
        get_path=["lng", "lat"], get_color=[0, 150, 255, 180],
    )
    capa_sectores = pdk.Layer(
        "ScatterplotLayer", df_sectores,
        get_position=["lng", "lat"], get_color=[46, 204, 113, 180], get_radius=RADIO_DETECCION_METROS,
    )

    # Capa de fondo con la imagen del circuito real
    img_b64 = get_circuit_image_base64()
    capa_fondo = pdk.Layer(
        "BitmapLayer",
        image=img_b64,
        bounds=[
            [MIN_LNG, MIN_LAT],  # suroeste
            [MIN_LNG, MAX_LAT],  # noroeste
            [MAX_LNG, MAX_LAT],  # nordeste
            [MAX_LNG, MIN_LAT]   # sudeste
        ],
        opacity=0.95
    )

    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/dark-v11",
        initial_view_state=pdk.ViewState(latitude=LAT_BASE, longitude=LNG_BASE, zoom=17.2, pitch=30),
        layers=[capa_fondo, capa_ruta, capa_sectores, capa_coche],
    ))

with col_datos:
    st.subheader("⏱️ Historial de Tiempos")
    
    # Renderizar panel de control de récords en una tabla/lista limpia
    for sec in ["Sector 1", "Sector 2", "Meta"]:
        ultimo = st.session_state.records_sectores[sec]["ultimo"]
        top3 = st.session_state.records_sectores[sec]["top3"]
        
        # Formatear el top 3 de manera vistosa
        top3_str = " | ".join([f"{t}s" for t in top3]) if top3 else "Sin registros"
        
        # Caja contenedora por sector
        with st.container(border=True):
            st.markdown(f"### 🏁 {sec}")
            c_ult, c_top = st.columns(2)
            c_ult.metric(label="Último Tiempo", value=f"{ultimo} s" if ultimo != "-" else "-")
            c_top.markdown(f"**🏆 Top 3 mejores:**\n`{top3_str}`")

    if st.session_state.vuelta_completa_flag:
        st.success(f"🏁 ¡VUELTA COMPLETA! Tiempo Total: {st.session_state.ultimo_total_vuelta} s")
    
    st.write("---")
    st.subheader("📊 Telemetría Simulada")
    
    c1, c2 = st.columns(2)
    c1.metric(label="Velocidad", value=f"{st.session_state.telemetria['vel']} km/h")
    c2.metric(label="Temp. Motor", value=f"{st.session_state.telemetria['temp']} °C")
    
    st.write("Tacómetro Dinámico")
    st.progress(min(int(st.session_state.telemetria['vel']), 160) / 160)
    
    st.write("Temperatura del Bloque")
    st.progress(min(int(st.session_state.telemetria['temp']), 110) / 110)

# Frecuencia de actualización
time.sleep(0.1)
st.rerun()