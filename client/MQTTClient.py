#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 11 11:15:56 2016
@author: sjj
"""

import datetime

print 'Starting...'
import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print "Connected with result code "+str(rc)

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.

    #https://www.thethingsnetwork.org/api/v0/gateways/B827EBFFFEE36EF8/
    # umang node https://www.thethingsnetwork.org/api/v0/nodes/A870D662/
    #sjj node https://www.thethingsnetwork.org/api/v0/nodes/4BE42396/
    #ttn1 B827EBFFFEE36EF8 - Roof
    # B827EBFFFE71AB02 - lanchester
    # B827EBFFFEE96E6E - 3rd
    #ttn2 = B827EBFFFE8E825E
    #"longitude":-1.40481,"latitude":50.93717

    client.subscribe("arduinoapp/devices/+/up", 0) #("+/devices/+/up" , 0 ) #("/70B3D57ED0000A45/devices/4BE42396/up", 0)
    #client.subscribe("70B3D57ED0000A73/devices/+/up" , 0 ) #("70B3D57ED0000A45/devices/000000004BE42396/up" , 0 ) #("+/devices/+/up" , 0 ) #("/70B3D57ED0000A45/devices/4BE42396/up", 0)

    print "here."

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print dir(msg)
    print msg.topic+" "+str(msg.payload)
    f = open('testing.json', 'a')
    f.write(str(datetime.datetime.now()))
    f.write(" " + str(msg.payload) + "\n")
    f.close()



def on_subscribe(client, userdata, mid, granted_qos):
    print "Subscribe" + mid


def on_log(client, userdata, level, buf):
    print str(level)+" "+str(buf)


client = mqtt.Client()
client.username_pw_set('arduinoapp', "ttn-account-v2.1tSVEHu5apF8huYcS7QEP79cQUVm6cjWwMl3_GkNpyE")
client.on_connect = on_connect
client.on_message = on_message
client.on_subscribe_subscribe = on_subscribe
client.on_log = on_log
client.connect("eu.thethings.network", 1883, 10)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
