from pytrack import Pytrack
from L76GNSS import L76GNSS
from network import LoRa, WLAN
from machine import SD
from machine import Timer
import os
import time
import socket
import json

import config
import binascii

from led import RgbWrapper

SD_MOUNT_DIR = "/sd"
GPS_FILENAME = "/gps"

def convert_payload(lat, lon, alt, hdop):
    payload= []
    latb = int(((lat + 90) / 180) * 0xFFFFFF)
    lonb = int(((lon + 180) / 360) * 0xFFFFFF)
    altb = int(round(float(alt),0))
    hdopb = int(float(hdop) * 10)

    payload.append(((latb >> 16) & 0xFF))
    payload.append(((latb >> 8) & 0xFF))
    payload.append((latb & 0xFF))
    payload.append(((lonb >> 16) & 0xFF))
    payload.append(((lonb >> 8) & 0xFF))
    payload.append((lonb & 0xFF))
    payload.append((altb & 0xFF))
    payload.append(hdopb & 0xFF)
    return payload


def write_coords(filename, time, lat, lon, alt, hdop):
    print(filename)
    f = open(filename, "a");
    d = {}
    d["time"] = time
    d["lat"] = lat
    d["lon"] = lon
    d["hdop"] = hdop
    d["alt"] = alt
    f.write(json.dumps(d))
    f.close()

rgb = RgbWrapper()  #Setup LED for debug output
sd_en = False       #Whether to try to write to SD card
chrono = Timer.Chrono() #Keep track of time since boot so can keep record of how long between GPS readings
chrono.start()      

try:
    sd = SD()
    os.mount(sd, SD_MOUNT_DIR)
    sd_en = True
    rgb.green(0x88)
    rgb.red(0x88)
    time.sleep(1)
    rgb.green_off()
    rgb.red_off()
except OSError:
    sd_en = False   #Make sure SD card access is disabled

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
print("Socket created")

while True:
    (lat, lon, alt, hdop) = gps.position()
    if not lat is None and not lon is None and not alt is None and not hdop is None: #Have a GPS fix
        if not fix:
            print("GPS lock acquired")
            fix = True
        rgb.red_off()
        rgb.green_on()
        print("%s %s %s %s" %(lat, lon, alt, hdop))
        payload = convert_payload(lat, lon, alt, hdop)
        sock.send(bytes(payload))
        #print(binascii.hexlify(bytes(payload)))
        try:
            write_coords(
                SD_MOUNT_DIR + GPS_FILENAME,
                chrono.read(),
                lat, lon, alt, hdop
                )
        except Exception:
            rgb.red_on()
            time.sleep(0.2)
            rgb.red_off()
            time.sleep(0.2)
            rgb.red_on()
            time.sleep(0.2)
            rgb.red_off()
        time.sleep(0.5)
        rgb.green_off()
        time.sleep(config.POST_MESSAGE_SLEEP)
        
    else:   #No GPS fix
        if fix:
            print("Lost GPS")
            fix = False
        rgb.red_on()
        time.sleep(1)
        rgb.red_off()
        time.sleep(1)
        rgb.red_on()
