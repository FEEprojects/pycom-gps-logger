"""
@author pjb
created 10/2017
"""

import binascii

def unpack_payload(payload):
    """
        Unpacks the compact binary format used by ttnmapper.org
    """
    lat, lon, alt, hdop = None, None, None, None
    payloadh = binascii.hexlify(payload)
    latb = int(payloadh[0:6], 16)
    lonb = int(payloadh[6:12], 16)
    alt = int(payloadh[12:16], 16)   #No further processing needed so direct to int
    hdopb = int(payloadh[16:18], 16)
    lat = round(((float(latb) / 0xFFFFFF) * 180) - 90, 5)
    lon = round(((float(lonb) / 0xFFFFFF) * 360) - 180, 5)
    hdop = float(hdopb)/10
    return (lat, lon, alt, hdop)

