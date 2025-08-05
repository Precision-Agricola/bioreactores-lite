# device/web_server.py

import uasyncio
import network
from microdot import Microdot, Response, send_file
from utils.logger import info, error
from hw.relay_controller import controller as relays
from sensors.flow_meter import flow_meter

WIFI_SSID = "Bio-Reactor-WiFi"
WIFI_PASSWORD = "password123"

app = Microdot()
Response.default_content_type = 'application/json'


@app.route('/')
async def serve_index(request):
    info("Web Server: Sirviendo index.html")
    return send_file("www/index.html")

@app.route('/api/status')
async def get_status(request):
    status = {
        "pump_on": relays.pump_is_on(),
        "flow_lpm": flow_meter.get_lpm()
    }
    return status

@app.route('/api/control', methods=['POST'])
async def control_actuators(request):
    try:
        data = request.json
        action = data.get("action")

        if action == "toggle_pump":
            relays.toggle_pump()
            info("Web API: Se ha conmutado la bomba.")
            return {"status": "success", "pump_on": relays.pump_is_on()}
        else:
            return {"status": "error", "message": "Acción no reconocida"}, 400

    except Exception as e:
        error(f"Error en API control: {e}")
        return {"status": "error", "message": "Petición inválida"}, 400

# --- Función de Arranque ---

async def start_server():
    # --- Inicio limpio de WiFi ---
    # Desactivar ambas interfaces para evitar conflictos de estado
    info("Realizando un inicio limpio de las interfaces Wi-Fi...")
    sta_if = network.WLAN(network.STA_IF)
    ap_if = network.WLAN(network.AP_IF)
    if sta_if.active():
        sta_if.active(False)
    if ap_if.active():
        ap_if.active(False)
    
    await uasyncio.sleep_ms(500) # Pequeña pausa para que se asienten los cambios

    info("Configurando modo Access Point...")
    ap_if.config(essid=WIFI_SSID, password=WIFI_PASSWORD)
    ap_if.active(True)

    while not ap_if.active():
        await uasyncio.sleep_ms(100)

    server_ip = ap_if.ifconfig()[0]
    info(f"Red Wi-Fi '{WIFI_SSID}' creada.")
    info(f"Conéctate y navega a http://{server_ip}")

    try:
        await app.start_server(host='0.0.0.0', port=80, debug=True)
    except Exception as e:
        error(f"No se pudo iniciar el servidor web: {e}")

