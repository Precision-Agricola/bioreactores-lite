# device/web_server.py

import uasyncio
import network
import json 
from microdot import Microdot, Response, send_file
from utils.logger import info, error
from hw.relay_controller import controller as relays
from sensors.flow_meter import flow_meter

WIFI_SSID = "Bio-Reactor-WiFi"
WIFI_PASSWORD = "password123"
SERVER_IP = '192.168.4.1'

app = Microdot()
Response.default_content_type = 'application/json'

@app.route('/')
async def server_index(request):
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

        if action == 'toggle_pump':
            relays.toggle_pump()
            info("Web API: se ha conmutado la bomba desde la api")
            return {"status": "success", "pump_on": relays.pump_is_on()}
        else:
            return {"status": "error", "message": "Accion no reconocida"}, 400
    
    except Exception as e:
        error(f"Error en api control : {e}") 
        return {"status": "error", "message": "Peticion invalida"}, 400


async def start_server():
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=WIFI_SSID, password=WIFI_PASSWORD)
    ap.active(True)

    while not ap.active():
        await uasyncio.sleep_ms(100)
    
    info(f"Red Wi-Fi '{WIFI_SSID}' creada")
    info(f"Conectate y Navega a http://{SERVER_IP}")

    try:
        await app.start_server(host=SERVER_IP, port=80)
    except Exception as e:
        error(f"No se puede iniciar el servidor web: {e}")
