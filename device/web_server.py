# device/web_server.py

import uasyncio
import network
import time
import gc
from microdot import Microdot, Response, send_file
from utils.logger import info, error
from hw.relay_controller import controller as relays
from sensors.flow_meter import flow_meter
from tasks import display_task

try:
    from config.system_version import VERSION, COMMIT, BUILD_DATE
except Exception:
    VERSION, COMMIT, BUILD_DATE = "dev", "local", "n/a"

WIFI_SSID = "Bio-Reactor-WiFi"
WIFI_PASSWORD = "password123"
MAX_WIFI_RETRIES = 3
_START_TIME_FILE = "start_time.txt"

app = Microdot()
Response.default_content_type = 'application/json'

inoculation_start_time = 0


@app.get('/health')
def health(req):
    return {
        "status": "ok",
        "version": VERSION,
        "commit": COMMIT,
        "build_date": BUILD_DATE
    }

def set_inoculation_start_time(timestamp):
    """Permite a main.py establecer la fecha de inicio."""
    global inoculation_start_time
    inoculation_start_time = timestamp
    info(f"Fecha de inicio de inoculación establecida en el servidor web: {inoculation_start_time}")

@app.route('/')
async def serve_index(request):
    """Sirve la página principal del dashboard."""
    info("Web Server: Sirviendo www/index.html")
    return send_file("www/index.html")
    
@app.route('/pa_dark_logo_with_letters.svg')
async def serve_logo(request):
    """Sirve el archivo del logo."""
    info("Web Server: Sirviendo logo SVG")
    return send_file("www/pa_dark_logo_with_letters.svg")

@app.route('/api/status')
async def get_status(request):
    """Endpoint para obtener el estado actual del sistema."""
    
    days_since_inoculation = 0
    if inoculation_start_time > 0:
        current_time = time.time()
        seconds_since_start = current_time - inoculation_start_time
        days_since_inoculation = int(seconds_since_start / 86400)

    comp_state = relays.compressors_state()
    aerator1_status = (comp_state == "A")
    aerator2_status = (comp_state == "B")

    status = {
        "pump_on": relays.pump_is_on(),
        "flow_lpm": flow_meter.get_lpm(),
        "inoculation_days": days_since_inoculation,
        "aerator1_on": aerator1_status,
        "aerator2_on": aerator2_status
    }
    return status

@app.route('/api/control', methods=['POST'])
async def control_actuators(request):
    """Endpoint para controlar los actuadores."""
    try:
        data = request.json
        action = data.get("action")

        if action == "toggle_pump":
            relays.toggle_pump()
            info("Web API: Se ha conmutado la bomba.")
            return {"status": "success", "pump_on": relays.pump_is_on()}
        
        elif action == "reset_inoculation":
            info("Web API: Reiniciando el conteo de inoculación.")
            new_start_time = time.time()
            
            with open(_START_TIME_FILE, "w") as f:
                f.write(str(new_start_time))
            
            set_inoculation_start_time(new_start_time)
            
            display_task.set_start_time(new_start_time)
            
            info(f"Nuevo tiempo de inicio guardado: {new_start_time}")
            return {"status": "success", "message": "Conteo de inoculación reiniciado."}
            
        else:
            return {"status": "error", "message": "Acción no reconocida"}, 400

    except Exception as e:
        error(f"Error en API control: {e}")
        return {"status": "error", "message": "Petición inválida"}, 400

async def start_server():
    gc.collect()
    info(f"Memoria libre al iniciar start_server: {gc.mem_free()} bytes")
    ap_if = network.WLAN(network.AP_IF)
    sta_if = network.WLAN(network.STA_IF)
    for attempt in range(MAX_WIFI_RETRIES):
        try:
            info(f"Intento de inicialización Wi-Fi #{attempt + 1}/{MAX_WIFI_RETRIES}...")
            if ap_if.active(): ap_if.active(False)
            if sta_if.active(): sta_if.active(False)
            await uasyncio.sleep(1)
            ap_if.config(essid=WIFI_SSID, password=WIFI_PASSWORD)
            ap_if.active(True)
            timeout_start = time.ticks_ms()
            while not ap_if.active():
                if time.ticks_diff(time.ticks_ms(), timeout_start) > 5000:
                    raise RuntimeError("Timeout al activar el AP")
                await uasyncio.sleep_ms(100)
            server_ip = ap_if.ifconfig()[0]
            info(f"Red Wi-Fi '{WIFI_SSID}' creada con éxito.")
            info(f"Conéctate y navega a http://{server_ip}")
            break
        except Exception as e:
            error(f"Fallo en el intento #{attempt + 1}: {e}")
            if attempt < MAX_WIFI_RETRIES - 1:
                info("Reintentando en 3 segundos...")
                await uasyncio.sleep(3)
            else:
                error("Todos los intentos de iniciar el Wi-Fi han fallado.")
                return
    if ap_if.active():
        try:
            info("Iniciando servidor web Microdot...")
            await app.start_server(host='0.0.0.0', port=80, debug=True)
        except Exception as e:
            error(f"No se pudo iniciar el servidor web Microdot: {e}")
