#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 11 11:15:56 2016
@author: sjj
Modified 09/2017
@author pjb
"""

import logging
import paho.mqtt.client as mqtt
from configobj import ConfigObj

DEFAULT_LOG_LEVEL = logging.WARN
LOGGER = None
CONFIG = None

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
    print msg.topic + " " + str(msg.payload)



def on_subscribe(client, userdata, mid, granted_qos):
    LOGGER.debug("Subscribe" + mid)


def on_log(client, userdata, level, buf):
    LOGGER.debug(str(level) + " " + str(buf))



def setup(config_file, log_level=DEFAULT_LOG_LEVEL):
    global LOGGER
    LOGGER = logging.getLogger("MQTT Client")
    LOGGER.setLevel(log_level)
    logging.basicConfig(format='%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
    global CONFIG
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
    client.loop_forever()

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
