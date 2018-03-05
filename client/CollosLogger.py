#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 11 11:15:56 2016
@author: sjj
Modified 09/2017
@author pjb
"""
import json
import logging
from optparse import OptionParser, OptionGroup
from datetime import datetime
from base64 import b64decode

import paho.mqtt.client as mqtt
from pymongo import MongoClient
from position_config import PositionLoggerConfig
from ttn_map_unpack import unpack_payload, TtnUnpackError

DEFAULT_CONFIG = "collos-config.ini"
DEFAULT_LOG_LEVEL = logging.INFO
LOGGER = None
CONFIG = None
DB = None
DB_CLIENT = None
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    LOGGER.info("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.


    client.subscribe(CONFIG.topic, CONFIG.qos)
    LOGGER.info("TOPIC: " + str(CONFIG.topic))
    LOGGER.info("QOS: " + str(CONFIG.qos))


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    db_data = {}
    device = data["dev_id"]
    payload = b64decode(data["payload_raw"])
    serial = data["hardware_serial"]
    timestamp = datetime.utcnow()
    try:
        (lat, lon, alt, hdop) = unpack_payload(payload)
        db_data["gps-position"] = {}
        db_data["gps-position"]["lon"] = lon
        db_data["gps-position"]["lat"] = lat
        db_data["gps-position"]["alt"] = alt
        db_data["gps-position"]["hdop"] = hdop
        LOGGER.info(
            timestamp.strftime("%Y-%m-%d %H:%M:%S") +  " " + str(serial)
            + " " + str(lat) + " " + str(lon) + " " + str(alt) + " " + str(hdop))
    except TtnUnpackError as e:
        LOGGER.error("Unable to unpack payload %s" % str(e))
    sf = data["metadata"]["data_rate"]
    gws = []    #object for passing to mongodb
    gateways = data["metadata"]["gateways"]
    for gate in gateways:
        gwd = {}    #dictionary for data from this gateway
        gwd["gw_id"] = gate["gtw_id"]
        gwd["snr"] = gate["snr"]
        gwd["rssi"] = gate["rssi"]
        gwd["timestamp"] = gate["timestamp"]
        gwd["time"] = gate["time"]
        gwd["channel"] = gate["channel"]
        try:
            gwd["antenna"] = gate["antenna"]
        except KeyError:
            gwd["antenna"] = 0     #Assume if not given it's antenna 0
        try:
            gwd["fine_timestamp"] = gate["fine_timestamp"]
        except KeyError:
            gwd["fine_timestamp"] = None
        try:
            gwd["fine_timestamp_encrypted"] = gate["fine_timestamp_encrypted"]
        except KeyError:
            gwd["fine_timestamp_encrypted"] = None
        gws.append(gwd)
    db_data["timestamp"] = timestamp
    db_data["sf"] = sf
    db_data["serial"] = serial
    db_data["collos-position"] = {}
    try:
        db_data["collos-position"]["lon"] = data["metadata"]["longitude"]
        db_data["collos-position"]["lat"] = data["metadata"]["latitude"]
        db_data["collos-position"]["location_source"] = data["metadata"]["location_source"]
    except KeyError:
        LOGGER.error("Unable to unpack Collos data")
    db_data["gateways"] = gws
    mongo_insert(db_data)

def mongo_insert(data):
    collection = DB[CONFIG.db_collection]
    collection.insert_one(data)
    LOGGER.debug("Inserted into DB")

def on_subscribe(client, userdata, mid, granted_qos):
    LOGGER.debug("Subscribe" + mid)


def on_log(client, userdata, level, buf):
    LOGGER.debug(str(level) + " " + str(buf))



def setup(config_file, log_level=DEFAULT_LOG_LEVEL):
    global LOGGER
    LOGGER = logging.getLogger("Collos Logger")
    LOGGER.setLevel(log_level)
    logging.basicConfig(format='%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
    global CONFIG
    CONFIG = PositionLoggerConfig(config_file)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_subscribe_subscribe = on_subscribe
    client.on_log = on_log
    LOGGER.debug("MQTT client created")
    client.username_pw_set(CONFIG.user, CONFIG.password)
    client.connect(CONFIG.server, CONFIG.port, CONFIG.keepalive)
    LOGGER.info("MQTT Server: " + CONFIG.server)
    LOGGER.info("MQTT Port: " + str(CONFIG.port))
    LOGGER.info("MQTT Keepalive: " + str(CONFIG.keepalive))
    LOGGER.info("MQTT Username: " + str(CONFIG.user))
    LOGGER.info("MQTT Password: " + str(CONFIG.password))

    global DB
    global DB_CLIENT
    DB_CLIENT = MongoClient(CONFIG.db_server, CONFIG.db_port)
    LOGGER.info("DB Server: " + CONFIG.db_server)
    LOGGER.info("DB Port: " + str(CONFIG.db_port))
    LOGGER.debug("MongoDB Client created")
    DB = DB_CLIENT[CONFIG.db_database]
    LOGGER.info("DB Database: " + str(CONFIG.db_database))
    LOGGER.info("DB Collection: " + str(CONFIG.db_collection))

    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        client.loop_stop()


if __name__ == "__main__":
    PARSER = OptionParser()
    LOG_LEVEL = DEFAULT_LOG_LEVEL
    LOG_GROUP = OptionGroup(
        PARSER, "Verbosity Options",
        "Options to change the level of output")
    LOG_GROUP.add_option(
        "-q", "--quiet", action="store_true",
        dest="quiet", default=False,
        help="Supress all but critical errors")
    LOG_GROUP.add_option(
        "-v", "--verbose", action="store_true",
        dest="verbose", default=False,
        help="Print all information available")
    PARSER.add_option_group(LOG_GROUP)
    PARSER.add_option(
        "-c", "--config", action="store",
        type="string", dest="config_file",
        help="Configuration file description options needed")
    (OPTIONS, ARGS) = PARSER.parse_args()
    if OPTIONS.quiet:
        LOG_LEVEL = logging.CRITICAL
    elif OPTIONS.verbose:
        LOG_LEVEL = logging.DEBUG
    if OPTIONS.config_file is None:
        CONFIG_FILE = DEFAULT_CONFIG
    else:
        CONFIG_FILE = OPTIONS.config_file
    setup(CONFIG_FILE, LOG_LEVEL)
#    try:
#        setup(CONFIG_FILE, LOG_LEVEL)
#    except Exception as EX:
#        print str(EX)
#        exit(1)
