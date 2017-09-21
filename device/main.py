from pytrack import Pytrack
from L76GNSS import L76GNSS
from network import LoRa
import time
import socket

import config
import binascii

from led import RgbWrapper

rgb = RgbWrapper()  #Setup LED for debug output

#Enable GPS here red on
rgb.red_on()
py = Pytrack()
gps = L76GNSS(py, timeout=config.GPS_TIMEOUT)

#Join Lora blue on
lora = LoRa(mode=LoRa.LORAWAN)
app_eui = binascii.unhexlify(config.APP_EUI)
app_key = binascii.unhexlify(config.APP_KEY)
lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=config.JOIN_TIMEOUT)
rgb.blue(0xFF)
while not lora.has_joined():
    time.sleep(1.25)
    rgb.blue(0x88)
    time.sleep(1.25)
    rgb.blue(0xFF)
print("Joined LoRaWAN network")
rgb.blue(0x88)
sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
sock.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
sock.setblocking(False)   

while True:
    (lat, lon) = gps.coordinates()
    if not lat is None and not lon is None: #We have a GPS fix
        rgb.red_off()
        rgb.green_on()
        msg = str(lat * 1000000) + " " + str(lon * 1000000)
        print(msg)
        sock.send(msg)
        time.sleep(0.5)
        rgb.green_off()
        time.sleep(config.POST_MESSAGE_SLEEP)
    else:   #No GPS fix
        rgb.red_on()
        time.sleep(1)
        rgb.red_off()
        time.sleep(1)
        rgb.red_on()
