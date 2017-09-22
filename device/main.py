from pytrack import Pytrack
from L76GNSS import L76GNSS
from network import LoRa, WLAN
import time
import socket

import config
import binascii

from led import RgbWrapper


def convert_payload(lat, lon, alt, hdop):
    payload= []
    latb = int(((lat + 90) / 180) * 0xFFFFFF)
    lonb = int(((lon + 180) / 360) * 0xFFFFFF)
    altb = int(float(alt) * 10)
    hdopb = int(float(hdop) * 10)

    payload.append(((latb >> 16) & 0xFF))
    payload.append(((latb >> 8) & 0xFF))
    payload.append((latb & 0xFF))
    payload.append(((lonb >> 16) & 0xFF))
    payload.append(((lonb >> 8) & 0xFF))
    payload.append((lonb & 0xFF))
    payload.append((altb >> 8) & 0xFF)
    payload.append((altb & 0xFF))
    payload.append(hdopb & 0xFF)
    return payload

rgb = RgbWrapper()  #Setup LED for debug output

wlan = WLAN()
wlan.deinit()   #Disable the WiFi access point

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
fix = False

while True:
    (lat, lon, alt, hdop) = gps.position() 
 #   lat = 123.456
 #   lon = 7.89
 #   alt = 86
 #   hdop = 4.33
    if not lat is None and not lon is None and not alt is None and not hdop is None: #We have a GPS fix
        if not fix:
            print("GPS lock acquired")
            fix = True
        rgb.red_off()
        rgb.green_on()  
        #print("%s %s %s %s" %(lat, lon, alt, hdop))
        payload = convert_payload(lat, lon, alt, hdop)
        sock.send(bytes(payload))
        #print(binascii.hexlify(bytes(payload)))
        time.sleep(0.5)
        rgb.green_off()
        time.sleep(config.POST_MESSAGE_SLEEP)
        
    else:   #No GPS fix
        if fix:
            print("Lost/No GPS")
            fix = False
        rgb.red_on()
        time.sleep(1)
        rgb.red_off()
        time.sleep(1)
        rgb.red_on()
