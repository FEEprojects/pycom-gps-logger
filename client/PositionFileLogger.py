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
from configobj import ConfigObj
import paho.mqtt.client as mqtt


from ttn_map_unpack import unpack_payload

DEFAULT_CONFIG = "position-config.ini"
DEFAULT_LOG_LEVEL = logging.INFO
LOGGER = None
CONFIG = None
FILENAME = None

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
    global FILENAME
    data = json.loads(msg.payload)
    device = data["dev_id"]
    payload = b64decode(data["payload_raw"])
    rate = data["metadata"]["data_rate"]
    (lat, lon, alt, hdop) = unpack_payload(payload)
    LOGGER.debug(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " + device  + " " + rate + " " + str(lat) + "" + str(lon) + " " + str(hdop) + " " + str(alt))
    gateways = data["metadata"]["gateways"]
    for gate in gateways:
        gw_id = gate["gtw_id"]
        snr = gate["snr"]
        rssi = gate["rssi"]
        print "\t" + str(gw_id) + "\t" + str(snr) + "\t" + str(rssi)
    data["lat"] = lat
    data["lon"] = lon
    data["alt"] = alt
    data["hdop"] = hdop
    try:
        if FILENAME is not None:    #Check we have a file to save to
            f = open(FILENAME, "a")
            f.write(json.dumps(data) + "\r\n")
            f.close()
    except Exception as e:
        print e
        LOGGER.error(e)
        FILENAME = None #clear filename to stop further attempts
        LOGGER.info("File write disabled")


def on_subscribe(client, userdata, mid, granted_qos):
    LOGGER.debug("Subscribe" + mid)


def on_log(client, userdata, level, buf):
    LOGGER.debug(str(level) + " " + str(buf))



def setup(config_file, filename=None, log_level=DEFAULT_LOG_LEVEL):
    global LOGGER
    global CONFIG
    global FILENAME
    LOGGER = logging.getLogger("MQTT Client")
    LOGGER.setLevel(log_level)
    logging.basicConfig(format='%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
    LOGGER.info("Target file: " + str(filename))
    CONFIG = MqttConfig(config_file)

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
    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        client.loop_stop()

class MqttConfig(object):
    def __init__(self, config_file):
        try:
            config = ConfigObj(config_file)
            self.user = config["user"]
            self.password = config["pass"]
            self.server = config["server"]
            self.port = int(config["port"])
            self.keepalive = int(config["keepalive"])
            self.topic = config["topic"]
            self.qos = int(config["qos"])
        except KeyError:
            raise ConfigError("Invalid configuration given, missing a required option")
        except ValueError:
            raise ConfigError("Number expected but string given")

class ConfigError(Exception):
    """
        Exception for use if the config file does not contain the required items
    """
    pass

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
    PARSER.add_option(
        "-f", "--filename", action="store",
        type="string", dest="target_file",
        help="Dump destination file")
    (OPTIONS, ARGS) = PARSER.parse_args()
    if OPTIONS.quiet:
        LOG_LEVEL = logging.CRITICAL
    elif OPTIONS.verbose:
        LOG_LEVEL = logging.DEBUG
    if OPTIONS.config_file is None:
        CONFIG_FILE = DEFAULT_CONFIG
    else:
        CONFIG_FILE = OPTIONS.config_file
    if OPTIONS.target_file is not None:
        FILENAME = OPTIONS.target_file

#    try:
    setup(CONFIG_FILE, FILENAME, LOG_LEVEL)
 #   except Exception as EX:
 #       print str(EX)
 #       exit(1)
