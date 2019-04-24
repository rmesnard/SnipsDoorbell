#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import json
import struct
from time import sleep
from snipsTools import *
import RPi.GPIO as GPIO
import sys

VERSION = '1.0.0'

config = SnipsConfigParser.read_configuration_file('/usr/share/snips/config/snips.toml')
config_common = config.get('snips-common')
config_doorbell = config.get('snips-doorbell')

MQTT_ADDR = str(config_common.get('mqtt')).replace('"', '')
SITE_ID = str(config_common.get('site_id')).replace('"', '')

#RELAY_GPIO = int(config_doorbell.get('relay_gpio_bcm'))
BUTTON_GPIO = int(config_doorbell.get('button_gpio_bcm'))

MQTT_PRESENCE = str(config_doorbell.get('mqtt_topic_presence')).replace('"', '')
MQTT_PRESENCE_PAYLOAD = str(config_doorbell.get('mqtt_payload_presence')).replace('"', '')

SAY_WLC_PRESENT = str(config_doorbell.get('say_welcome_present')).replace('"', '')
SAY_WLC_NOTPRESENT = str(config_doorbell.get('say_welcome_nopresent')).replace('"', '')
SAY_GOODB = str(config_doorbell.get('say_goobye')).replace('"', '')
SAY_START_MSG = str(config_doorbell.get('say_start_message')).replace('"', '')

#relay = RelaySwitch.RelaySwitch('relay', RELAY_GPIO)
button_status = False
previous_status = False

# Default True
presence = False
runphase = 0

def on_connect(client, userdata, flags, rc):
    print('Connected to MQTT system')
    mqtt.subscribe('snips/doorbell/' + SITE_ID )
    mqtt.subscribe('hermes/intent/#')
    mqtt.subscribe('hermes/dialogueManager/#')
    if MQTT_PRESENCE != "":
        mqtt.subscribe(MQTT_PRESENCE)

def on_message(client, userdata, msg):
    global presence
    global runphase
    print('msg.topic ' + msg.topic)
    if msg.topic == "snips/doorbell/" + SITE_ID:
        doorbell_command(msg)
    if msg.topic == MQTT_PRESENCE:
        if msg.payload == MQTT_PRESENCE_PAYLOAD:
            presence = True
        else:
            presence = False
    if msg.topic == "hermes/intent/rmesnard:getmessage":
        if runphase==2:
            doorbell_recordmessage(msg)
    if msg.topic == "hermes/intent/rmesnard:sayyes":
        if runphase==2:
            doorbell_recordmessage(msg)
    if msg.topic == "hermes/intent/rmesnard:sayno":
        if runphase==2:
            doorbell_seeyou(msg)

def doorbell_seeyou(msg):
    global runphase
    global sessionId
    print("end")
    runphase=0
    m_decode=str(msg.payload.decode("utf-8","ignore"))
    m_in=json.loads(m_decode) #decode json data
    sessionId = m_in["sessionId"]
    mqtt.publish("hermes/dialogueManager/endSession",'{"sessionId":"'+ sessionId +'" , "text":"'+  SAY_GOODB +'" }')  


def doorbell_command(msg):
    m_decode=str(msg.payload.decode("utf-8","ignore"))
    #print("data Received type",type(m_decode))
    #print("data Received",m_decode)
    #print("Converting from Json to Object")
    m_in=json.loads(m_decode) #decode json data
    print("command = ",m_in["command"])
    #print("channel = ",m_in["channel"])
    if m_in["command"] == "ring":
        ringing()      
        
def doorbell_recordmessage(msg):
    global runphase
    global sessionId
    print("record")
    runphase=3
    m_decode=str(msg.payload.decode("utf-8","ignore"))
    m_in=json.loads(m_decode) #decode json data
    sessionId = m_in["sessionId"]
    mqtt.publish("hermes/dialogueManager/endSession",'{"sessionId":"'+ sessionId +'" , "text":"'+  SAY_START_MSG +'" }')  

def ringing():
    global runphase
    global presence
    print('ringing')
    if (presence):
        runphase=1
        mqtt.publish("hermes/dialogueManager/startSession",'{"siteId":"'+ SITE_ID +'" , "init" : { "type" : "action" ,"text":"'+  SAY_WLC_PRESENT +'"} }')
    else:
        runphase=2
        mqtt.publish("hermes/dialogueManager/startSession",'{"siteId":"'+ SITE_ID +'" , "init" : { "type" : "action" ,"text":"'+  SAY_WLC_NOTPRESENT +'" , "intentFilter" : [ "rmesnard:getmessage" , "rmesnard:sayyes" , "rmesnard:sayno" ] } }')

def main():
    global previous_status
    global button_status

    try:
        mqtt_parse = MQTT_ADDR.split(":")
        print("connecting to : "+ MQTT_ADDR)
       
        mqtt.on_connect = on_connect
        mqtt.on_message = on_message
        mqtt.connect(str(mqtt_parse[0]), int(mqtt_parse[1]))

        print("push button on GPIO " + str(BUTTON_GPIO))
        GPIO.setwarnings(False)
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_GPIO, GPIO.IN)
        
        while True:
            #process mqtt message
            mqtt.loop()
            #check the push button
            button_status = GPIO.input(BUTTON_GPIO)
            if (button_status == False) and ( button_status != previous_status) :
                mqtt.publish("snips/doorbell/"+ SITE_ID,'{"command":"ring"}') 
                previous_status=button_status

            if button_status:
                previous_status=button_status

    except KeyboardInterrupt: 
        print("End.")
    except:
        print("Unexpected error:", sys.exc_info()[0])
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    mqtt = mqtt.Client(SITE_ID)
    main()