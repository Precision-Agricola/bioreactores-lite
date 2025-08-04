# device/web_server.py

import uasyncio
import network
import json 
from microdot import Microdot, Response, send_file
from utils.logger