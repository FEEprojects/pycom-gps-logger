"""
Uses the pytrack module with the pycom to record the position
and then transmit it over LoRaWAN to enable range testing.

Also records GPS locations to µSD card for further debug.
In theory this recording starts before LoRa signal is gathered
but this part is currently untested.
@author Philip Basford
"""

import os
import time
import socket
import json
import binascii
import config
import struct

from pytrack import Pytrack
from L76GNSS import L76GNSS
from network import LoRa, WLAN
from machine import SD
from machine import Timer


from led import RgbWrapper

SD_MOUNT_DIR = "/sd"
GPS_FILENAME = "/gps.log"


def convert_payload(lat, lon, alt, hdop):
    """
        Converts to the format used by ttnmapper.org
    """
    payload = []
    latb = int(((lat + 90) / 180) * 0xFFFFFF)
    lonb = int(((lon + 180) / 360) * 0xFFFFFF)
    altb = int(round(float(alt), 0))
    hdopb = int(float(hdop) * 10)

    payload.append(((latb >> 16) & 0xFF))
    payload.append(((latb >> 8) & 0xFF))
    payload.append((latb & 0xFF))
    payload.append(((lonb >> 16) & 0xFF))
    payload.append(((lonb >> 8) & 0xFF))
    payload.append((lonb & 0xFF))
    payload.append(((altb  >> 8) & 0xFF))
    payload.append((altb & 0xFF))
    payload.append(hdopb & 0xFF)
    return payload


def write_coords(filename, time, lat, lon, alt, hdop):
    """
        Writes out the co-ordinates and time since boot out to file.  
        Each line is a JSON object, they are not in an array as that would mean the file
        can't just be appended to
    """
    print(filename)
    f = open(filename, "a")
    d = {}
    d["time"] = time
    d["lat"] = lat
    d["lon"] = lon
    d["hdop"] = hdop
    d["alt"] = alt
    f.write(json.dumps(d))
    f.write("\n")
    f.close()
    rgb.green(0x88)
    rgb.red(0x88)
    time.sleep(1)
    rgb.green_off()
    rgb.red_off()

def has_moved(lon, lat, prev_lon, prev_lat, threshold=0.0005):
    """
        Compare readings to work out if it has moved enough for it to be worth while
        0.0005 is finest grained details shown on map equates to ~55m accuracy
    """
    abs_lat_difference = abs(prev_lat - lat)
    if abs_lat_difference > threshold:
        #we've moved enough in this direction that the lon doesn't matter
        return True
    else:
        abs_lon_difference = abs(prev_lon - lon)
        return abs_lon_difference > threshold




rgb = RgbWrapper()  #Setup LED for debug output
sd_en = False       #Whether to try to write to SD card
chrono = Timer.Chrono() #Keep track of time since boot so can  record how long between GPS readings
chrono.start()
last_gps_reading = 0    #When the last GPS reading was taken

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
print("SD Card enabled: " + str(sd_en))

wlan = WLAN()
wlan.deinit()   #Disable the WiFi access point

#Enable GPS here red on
rgb.red_on()
py = Pytrack()
gps = L76GNSS(py, timeout=config.GPS_TIMEOUT)
fix = False     #Initially we don't have a fix

#Join Lora blue on
lora = LoRa(mode=LoRa.LORAWAN)
dev_addr = struct.unpack(">l", binascii.unhexlify(config.DEV_ADDR))[0]
nwk_swkey = binascii.unhexlify(config.NWS_KEY)
app_swkey = binascii.unhexlify(config.APPS_KEY)
lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey))
prev_lat = 0 
prev_lon = 0
# will mean that if it's first turned on off the african coast then it will think it hasn't moved 
# and therefore won't transmit a packet, considered a low risk issue

while not lora.has_joined():
    time.sleep(1.25)
    time.sleep(1.25)
    rgb.blue_off()
    if sd_en:   #No point in trying to get a GPS fix if no SD card as nowhere to store it
        if (chrono.read() - last_gps_reading) > config.GPS_READ_INTERVAL:
            print("Performing a GPS read to log to SD")
        (lat, lon, alt, hdop) = gps.position()
        last_gps_reading = chrono.read() #record time of the last attempt to read GPS
        if(not lat is None
           and not lon is None
           and not alt is None
           and not hdop is None): #Have a GPS fix
            if not fix:
                print("GPS lock acquired")
                fix = True
                rgb.red_off()
        else:   #No GPS fix
            if fix:
                print("Lost GPS")
                fix = False
                rgb.red_on()
print("Joined LoRaWAN network")
sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
sock.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)
sock.setblocking(False)

print("Socket created")
while True:
    (lat, lon, alt, hdop) = gps.position()
    if not lat is None and not lon is None and not alt is None and not hdop is None: #Have a GPS fix
        if not fix:
            print("GPS lock acquired")
            fix = True
        rgb.red_off()
        
        print("%s %s %s %s" %(lat, lon, alt, hdop))
        if has_moved(lon, lat, prev_lon, prev_lat): #it's moved since last checked
            print("moved")
            payload = convert_payload(lat, lon, alt, hdop)
            sock.send(bytes(payload))
            prev_lon = lon
            prev_lat = lat
            rgb.green_on()
            time.sleep(0.5)
            rgb.green_off()
        else:
            print("Stationary")
            rgb.blue_on()
            time.sleep(0.5)
            rgb.blue_off()
        #print(binascii.hexlify(bytes(payload)))
        try:
            if sd_en:  #Only try writing to SD card if it's enabled
                print("SD Write")
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
            sd_en = False   #Stop trying to write to SD card

        time.sleep(config.POST_MESSAGE_SLEEP)
    else:   #No GPS fix
        if fix:
            print("Lost GPS")
            fix = False
            rgb.red_on()

