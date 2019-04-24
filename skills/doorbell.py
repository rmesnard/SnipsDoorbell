#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import json
import struct
from threading import Timer
from snipsTools import *
import RPi.GPIO as GPIO
import sys

VERSION = '1.0.0'

config = SnipsConfigParser.read_configuration_file('/usr/share/snips/config/snips.toml')
config_common = config.get('snips-common')
config_doorbell = config.get('snips-doorbell')

MQTT_ADDR = str(config_common.get('mqtt')).replace('"', '')
SITE_ID = str(config_common.get('site_id')).replace('"', '')

MQTT_SNIPSHOME = str(config_doorbell.get('mqtt_homestation')).replace('"', '')

#RELAY_GPIO = int(config_doorbell.get('relay_gpio_bcm'))
#PIR_GPIO = int(config_doorbell.get('pir_gpio_bcm'))
BUTTON_GPIO = int(config_doorbell.get('button_gpio_bcm'))

RETRY_ASKHOME = int(config_doorbell.get('retry_ask_home'))
TIMER_RECORD = int(config_doorbell.get('timer_record'))
TIMER_ASKHOME = int(config_doorbell.get('timer_ask_home'))


MQTT_PRESENCE = str(config_doorbell.get('mqtt_topic_presence')).replace('"', '')
MQTT_PRESENCE_PAYLOAD = str(config_doorbell.get('mqtt_payload_presence')).replace('"', '')

SAY_WLC_PRESENT = str(config_doorbell.get('say_welcome_present')).replace('"', '')
SAY_WLC_NOTPRESENT = str(config_doorbell.get('say_welcome_nopresent')).replace('"', '')
SAY_GOODB = str(config_doorbell.get('say_goobye')).replace('"', '')
SAY_START_MSG = str(config_doorbell.get('say_start_message')).replace('"', '')
SAY_NOREPLY = str(config_doorbell.get('say_no_reply')).replace('"', '')
SAY_INCOMMING = str(config_doorbell.get('say_incomming')).replace('"', '')

button_status = False
previous_status = False

retry_call = 0
# Default presence  True  
presence = True
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
    #print('msg.topic ' + msg.topic)
    if msg.topic == 'snips/doorbell/' + SITE_ID:
        doorbell_command(msg)
    if msg.topic == MQTT_PRESENCE:
        if msg.payload == MQTT_PRESENCE_PAYLOAD:
            presence = True
        else:
            presence = False
    if msg.topic == 'hermes/intent/rmesnard:getmessage':
        if runphase==4:
            doorbell_recordmessage(msg)
    if msg.topic == 'hermes/intent/rmesnard:sayyes':
        if runphase==4:
            doorbell_recordmessage(msg)
    if msg.topic == 'hermes/intent/rmesnard:sayno':
        if runphase==4:
            print("sayno")
            doorbell_seeyou(msg,True)
    if msg.topic == 'hermes/dialogueManager/sessionEnded':
        m_decode=str(msg.payload.decode("utf-8","ignore"))
        m_in=json.loads(m_decode) 
        sessionId = m_in["sessionId"]
        siteId = m_in["siteId"]
        customData = m_in["customData"]
        if runphase==1 and customData == 'RINGING' and siteId == MQTT_SNIPSHOME :
            ring_retry()
        if runphase==4 and customData == 'ASK_MESSAGE' and siteId == SITE_ID :
            doorbell_seeyou(msg,False)

def on_timer():
    global retry_call
    global runphase
    print('time out')
    if runphase == 1 :
        print('no answser at home')
        #mqtt.publish('hermes/dialogueManager/startSession','{"siteId":"'+ SITE_ID +'" , "init" : { "type" : "action" ,"text":"'+  SAY_WLC_NOTPRESENT +'" , "intentFilter" : [ "rmesnard:getmessage" , "rmesnard:sayyes" , "rmesnard:sayno" ] } }')
        runphase = 4
        retry_call = 0
        mqtt.publish('hermes/dialogueManager/startSession','{"siteId":"'+ SITE_ID +'", "customData" : "ASK_MESSAGE" , "init" : { "type" : "action" ,"text":"'+  SAY_NOREPLY +'" , "intentFilter" : [ "rmesnard:getmessage" , "rmesnard:sayyes" , "rmesnard:sayno" ] } }')        


def doorbell_seeyou(msg,sessionexist):
    global runphase
    global sessionId
    print("end")
    runphase=0
    if sessionexist :
        m_decode=str(msg.payload.decode("utf-8","ignore"))
        m_in=json.loads(m_decode) #decode json data
        sessionId = m_in["sessionId"]
        mqtt.publish('hermes/dialogueManager/endSession','{"sessionId":"'+ sessionId +'" , "text":"'+  SAY_GOODB +'" }')  
    else:
        mqtt.publish('hermes/dialogueManager/startSession','{"siteId":"'+ SITE_ID +'" , "init" : { "type" : "notification" ,"text":"'+  SAY_GOODB +'"} }')
    doorbell_stoprecordmessage()
    doorbell_closeaudioIN()



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
    mqtt.publish('hermes/dialogueManager/endSession','{"sessionId":"'+ sessionId +'" , "text":"'+  SAY_START_MSG +'" }')  

def doorbell_startrecordmessage():
    print ("start recording on " + MQTT_SNIPSHOME )
    #mqtt.publish('snips/audioClient/' + MQTT_SNIPSHOME,'{ "channel":"'+ SITE_ID +'" , "command" : "startrecord" }')

def doorbell_openaudioIN():
    print ("audio IN - On : " + MQTT_SNIPSHOME)
    mqtt.publish('snips/audioClient/' + MQTT_SNIPSHOME,'{ "channel":"'+ SITE_ID +'" , "command" : "startplay" }')
    
def doorbell_stoprecordmessage():
    print ("stop recording on " + MQTT_SNIPSHOME )
    #mqtt.publish('snips/audioClient/' + MQTT_SNIPSHOME,'{ "channel":"'+ SITE_ID +'" , "command" : "stoprecord" }')

def doorbell_closeaudioIN():
    print ("audio IN - Off : " + MQTT_SNIPSHOME)
    mqtt.publish('snips/audioClient/' + MQTT_SNIPSHOME,'{ "channel":"'+ SITE_ID +'" , "command" : "stopplay" }')

def ringing():
    global runphase
    global presence
    global retry_call
    print('ringing')
    retry_call = 0
    if (presence):
        runphase=1
        mqtt.publish('hermes/dialogueManager/startSession','{"siteId":"'+ SITE_ID +'" , "init" : { "type" : "notification" ,"text":"'+  SAY_WLC_PRESENT +'"} }')
        mqtt.publish('hermes/dialogueManager/startSession','{"siteId":"'+ MQTT_SNIPSHOME +'" , "init" : { "type" : "action" ,"text":"'+  SAY_INCOMMING +'" , "customData" : "SAY_INCOMMING" } }')
        doorbell_startrecordmessage()
        doorbell_openaudioIN()
        tmr = Timer(TIMER_ASKHOME, on_timer)
        tmr.start()
    else:
        runphase=4
        mqtt.publish('hermes/dialogueManager/startSession','{"siteId":"'+ SITE_ID +'" , "customData" : "ASK_MESSAGE" , "init" : { "type" : "action" ,"text":"'+  SAY_WLC_NOTPRESENT +'" , "customData" : "ASK_MESSAGE" , "intentFilter" : [ "rmesnard:getmessage" , "rmesnard:sayyes" , "rmesnard:sayno" ] } }')

def ring_retry():
    global runphase
    global retry_call

    if (retry_call >= RETRY_ASKHOME ):
        print('time out')
        runphase = 4
        retry_call = 0
        mqtt.publish('hermes/dialogueManager/startSession','{"siteId":"'+ SITE_ID +'" , "init" : { "type" : "action" ,"text":"'+  SAY_NOREPLY +'"  , "customData" : "ASK_MESSAGE" , "intentFilter" : [ "rmesnard:getmessage" , "rmesnard:sayyes" , "rmesnard:sayno" ] } }')        
    else:
        print('ringing retry')
        retry_call+=1
        mqtt.publish('hermes/dialogueManager/startSession','{"siteId":"'+ MQTT_SNIPSHOME +'" , "init" : { "type" : "notification" ,"text":"'+  SAY_INCOMMING +'" , "customData" : "RINGING" } }')


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
                mqtt.publish('snips/doorbell/'+ SITE_ID,'{"command":"ring"}') 
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