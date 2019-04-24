#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import json
import struct
from threading import Timer 
from snipsTools import *
import RPi.GPIO as GPIO
import wave
import datetime
import os
import sys
import alsaaudio

VERSION = '1.0.0'

config = SnipsConfigParser.read_configuration_file('/usr/share/snips/config/snips.toml')
config_common = config.get('snips-common')
config_doorbell = config.get('snips-doorbell')
config_audio = config.get('snips-audio-player')

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
MQTT_MESSAGE = str(config_doorbell.get('mqtt_topic_message')).replace('"', '')

SAY_WLC_PRESENT = str(config_doorbell.get('say_welcome_present')).replace('"', '')
SAY_WLC_NOTPRESENT = str(config_doorbell.get('say_welcome_nopresent')).replace('"', '')
SAY_GOODB = str(config_doorbell.get('say_goobye')).replace('"', '')
SAY_START_MSG = str(config_doorbell.get('say_start_message')).replace('"', '')
SAY_NOREPLY = str(config_doorbell.get('say_no_reply')).replace('"', '')
SAY_INCOMMING = str(config_doorbell.get('say_incomming')).replace('"', '')
SAY_THANKS = str(config_doorbell.get('say_thanks')).replace('"', '')

SAY_NO_MESSAGE = str(config_doorbell.get('say_no_message')).replace('"', '')
SAY_XXX_MESSAGE = str(config_doorbell.get('say_xxx_messages')).replace('"', '')
SAY_MESSAGE_XXX = str(config_doorbell.get('say_message_xxx')).replace('"', '')

AUDIO_OUT = str(config_audio.get('audio_out')).replace('"', '')
AUDIO_CHANNELS = int(config_audio.get('channels'))
AUDIO_BITRATE = int(config_audio.get('bitrate'))
AUDIO_PERIOD = int(config_audio.get('periodsize'))

RECORD_PATH = str(config_audio.get('record_path')).replace('"', '')

stream_play = ""
stream_record = ""


record_running = False
output_device1 = alsaaudio.PCM(alsaaudio.PCM_PLAYBACK, alsaaudio.PCM_NONBLOCK, AUDIO_OUT)
output_device1.setchannels(AUDIO_CHANNELS)
output_device1.setrate(AUDIO_BITRATE)
output_device1.setformat(alsaaudio.PCM_FORMAT_S16_LE)
output_device1.setperiodsize(AUDIO_PERIOD)    

button_status = False
previous_status = False

retry_call = 0
# Default presence  True  
presence = True
runphase = 0
session_id_doorbell = ''
session_id_home = ''

nb_recorded_message = 0

def on_connect(client, userdata, flags, rc):
    print('Connected to MQTT system')
    mqtt.subscribe('snips/audioClient/' + SITE_ID )
    mqtt.subscribe('snips/doorbell/' + SITE_ID )
    mqtt.subscribe('hermes/intent/#')
    mqtt.subscribe('hermes/dialogueManager/#')
    mqtt.subscribe('hermes/tts/sayFinished')
    if MQTT_MESSAGE != "":
        mqtt.subscribe(MQTT_MESSAGE)
    if MQTT_PRESENCE != "":
        mqtt.subscribe(MQTT_PRESENCE)

def on_message(client, userdata, msg):
    global presence
    global runphase
    global session_id_doorbell
    global session_id_home
    global nb_recorded_message
    global stream_play
    global stream_record

    #print('msg.topic ' + msg.topic)
    #print('msg.payload ' + str(msg.payload))
    if msg.topic == "snips/audioClient/" + SITE_ID:
        audioclient_command(msg)
    else:
        
        act_play = False
        act_record = False
        if msg.topic == "hermes/audioServer/" + stream_play + "/audioFrame":
            act_play = True
            streamid = stream_play

        if msg.topic == "hermes/audioServer/" + stream_record + "/audioFrame":
            act_record = True
            streamid = stream_record
        if act_play or act_record:
            process_streamaudio(streamid, msg, act_play, act_record)


        if msg.topic == 'snips/doorbell/' + SITE_ID:
            doorbell_command(msg)
        if msg.topic == MQTT_PRESENCE:
            if msg.payload == MQTT_PRESENCE_PAYLOAD:
                presence = True
            else:
                presence = False
        if msg.topic == MQTT_MESSAGE:
            print('messages count')
            nb_recorded_message = int(msg.payload)

        if msg.topic == 'hermes/intent/rmesnard:readmessage':
            if runphase==0:
                doorbell_readmessages(msg)

        if msg.topic == 'hermes/intent/rmesnard:getmessage':
            if runphase==0:
                doorbell_readmessages(msg)        
            if runphase==4:
                doorbell_recordmessage(msg)
            if runphase==1:
                runphase=4
                mqtt.publish('hermes/dialogueManager/startSession','{"siteId":"'+ SITE_ID +'" , "customData" : "ASK_MESSAGE" , "init" : { "type" : "action" ,"text":"'+  SAY_NOREPLY +'" , "intentFilter" : [ "rmesnard:getmessage" , "rmesnard:sayyes" , "rmesnard:sayno" ] } }')
                print("ask for message")

        if msg.topic == 'hermes/intent/rmesnard:sayyes':
            if runphase==4:
                doorbell_recordmessage(msg)

        if msg.topic == 'hermes/intent/rmesnard:sayno':
            if runphase==4:
                print("sayno")
                doorbell_seeyou(msg,True)

        if msg.topic == 'hermes/intent/rmesnard:reply':
            if runphase==1:
                print("reply")
                doorbell_connectaudio(msg)

        if msg.topic == 'hermes/intent/rmesnard:endconnection':
            if runphase==2:
                print("disconnect")
                doorbell_seeyou(msg,False)

        if msg.topic == 'hermes/dialogueManager/sessionEnded':
            m_decode=str(msg.payload.decode("utf-8","ignore"))
            m_in=json.loads(m_decode) 
            siteId = m_in["siteId"]
            customData = m_in["customData"]
            if runphase==1 and customData == 'RINGING' and siteId == MQTT_SNIPSHOME :
                ring_retry()
            if runphase==4 and customData == 'ASK_MESSAGE' and siteId == SITE_ID :
                doorbell_seeyou(msg,False)
        if msg.topic == 'hermes/dialogueManager/sessionStarted':
            m_decode=str(msg.payload.decode("utf-8","ignore"))
            m_in=json.loads(m_decode) 
            sessionId = m_in["sessionId"]
            siteId = m_in["siteId"]
            if siteId == SITE_ID :
                session_id_doorbell = sessionId
            if siteId == MQTT_SNIPSHOME :
                session_id_home = sessionId
        if msg.topic == 'hermes/tts/sayFinished':
            m_decode=str(msg.payload.decode("utf-8","ignore"))
            m_in=json.loads(m_decode) 
            sessionId = m_in["sessionId"]
            if runphase==1 and sessionId==session_id_doorbell:
                doorbell_startrecordmessage()
                doorbell_openaudioIN()


def on_timer():
    global retry_call
    global runphase
    print('time out')
    if runphase == 1 :
        print('no answser at home')
        runphase = 4
        retry_call = 0
        mqtt.publish('hermes/dialogueManager/startSession','{"siteId":"'+ SITE_ID +'", "customData" : "ASK_MESSAGE" , "init" : { "type" : "action" ,"text":"'+  SAY_NOREPLY +'" , "intentFilter" : [ "rmesnard:getmessage" , "rmesnard:sayyes" , "rmesnard:sayno" ] } }')        
    if runphase == 5 :
        doorbell_endrecord()


def doorbell_endrecord():
    global runphase
    print("end record")
    runphase=0
    mqtt.publish('hermes/dialogueManager/startSession','{"siteId":"'+ SITE_ID +'" , "init" : { "type" : "notification" ,"text":"'+  SAY_THANKS +'"} }')
    doorbell_stoprecordmessage()
    doorbell_closeaudioIN()

def doorbell_connectaudio(msg):
    global runphase
    runphase=2
    doorbell_openaudioOUT()

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
    doorbell_closeaudioOUT()

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
    global nb_recorded_message

    print("record")
    runphase=5
    m_decode=str(msg.payload.decode("utf-8","ignore"))
    m_in=json.loads(m_decode) #decode json data
    sessionId = m_in["sessionId"]
    mqtt.publish('hermes/dialogueManager/endSession','{"sessionId":"'+ sessionId +'" , "text":"'+  SAY_START_MSG +'" }') 
    if MQTT_MESSAGE != "":
        nb_recorded_message+=1 
        mqtt.publish(MQTT_MESSAGE,nb_recorded_message,0,True)  
    tmr = Timer(TIMER_RECORD, on_timer)
    tmr.start()

def doorbell_startrecordmessage():
    print ("start recording on " + MQTT_SNIPSHOME )
    mqtt.publish('snips/audioClient/' + MQTT_SNIPSHOME,'{ "channel":"'+ SITE_ID +'" , "command" : "startrecord" }')

def doorbell_openaudioIN():
    print ("audio IN - On : " + MQTT_SNIPSHOME)
    mqtt.publish('snips/audioClient/' + MQTT_SNIPSHOME,'{ "channel":"'+ SITE_ID +'" , "command" : "startplay" }')
    
def doorbell_openaudioOUT():
    print ("audio OUT - On : " + MQTT_SNIPSHOME)
    mqtt.publish('snips/audioClient/' + SITE_ID,'{ "channel":"'+ MQTT_SNIPSHOME +'" , "command" : "startplay" }')

def doorbell_stoprecordmessage():
    print ("stop recording on " + MQTT_SNIPSHOME )
    mqtt.publish('snips/audioClient/' + MQTT_SNIPSHOME,'{ "channel":"'+ SITE_ID +'" , "command" : "stoprecord" }')

def doorbell_closeaudioIN():
    print ("audio IN - Off : " + MQTT_SNIPSHOME)
    mqtt.publish('snips/audioClient/' + MQTT_SNIPSHOME,'{ "channel":"'+ SITE_ID +'" , "command" : "stopplay" }')

def doorbell_closeaudioOUT():
    print ("audio OUT - Off : " + MQTT_SNIPSHOME)
    mqtt.publish('snips/audioClient/' + SITE_ID,'{ "channel":"'+ MQTT_SNIPSHOME +'" , "command" : "stopplay" }')

def ringing():
    global runphase
    global presence
    global retry_call

    print('ringing')
    retry_call = 0
    if (presence):
        runphase=1
        mqtt.publish('hermes/dialogueManager/startSession','{"siteId":"'+ SITE_ID +'" , "init" : { "type" : "notification" ,"text":"'+  SAY_WLC_PRESENT +'"} }')
        mqtt.publish('hermes/dialogueManager/startSession','{"siteId":"'+ MQTT_SNIPSHOME +'" , "customData" : "RINGING"  , "init" : { "type" : "action" ,"text":"'+  SAY_INCOMMING +'" , "intentFilter" : [ "rmesnard:reply" , "rmesnard:getmessage" , "rmesnard:asktowait"  ] } }')
        tmr = Timer(TIMER_ASKHOME, on_timer)
        tmr.start()
    else:
        runphase=4
        mqtt.publish('hermes/dialogueManager/startSession','{"siteId":"'+ SITE_ID +'" , "customData" : "ASK_MESSAGE" , "init" : { "type" : "action" ,"text":"'+  SAY_WLC_NOTPRESENT +'" , "intentFilter" : [ "rmesnard:getmessage" , "rmesnard:sayyes" , "rmesnard:sayno" ] } }')

def ring_retry():
    global runphase
    global retry_call

    if (retry_call >= RETRY_ASKHOME ):
        print('time out')
        runphase = 4
        retry_call = 0
        mqtt.publish('hermes/dialogueManager/startSession','{"siteId":"'+ SITE_ID +'" , "customData" : "ASK_MESSAGE" , "init" : { "type" : "action" ,"text":"'+  SAY_NOREPLY +'"   , "intentFilter" : [ "rmesnard:getmessage" , "rmesnard:sayyes" , "rmesnard:sayno" ] } }')        
    else:
        print('ringing retry')
        retry_call+=1
        mqtt.publish('hermes/dialogueManager/startSession','{"siteId":"'+ MQTT_SNIPSHOME +'" , "customData" : "RINGING" , "init" : { "type" : "action" ,"text":"'+  SAY_INCOMMING +'"  , "intentFilter" : [ "rmesnard:reply" , "rmesnard:getmessage" , "rmesnard:asktowait" ] } }')

def doorbell_readmessages(msg):
    global nb_recorded_message

    if nb_recorded_message > 0:
        nmessg = SAY_XXX_MESSAGE.replace('XXX', str(nb_recorded_message))
        mqtt.publish('hermes/dialogueManager/startSession','{"siteId":"'+ SITE_ID +'" , "init" : { "type" : "notification" ,"text":"'+  nmessg +'"} }')
        # TODO READ the messages
    else:
        mqtt.publish('hermes/dialogueManager/startSession','{"siteId":"'+ SITE_ID +'" , "init" : { "type" : "notification" ,"text":"'+  SAY_NO_MESSAGE +'"} }')

def audioclient_command(msg):
    m_decode=str(msg.payload.decode("utf-8","ignore"))
    #print("data Received type",type(m_decode))
    #print("data Received",m_decode)
    #print("Converting from Json to Object")
    m_in=json.loads(m_decode) #decode json data
    print("command = ",m_in["command"])
    print("channel = ",m_in["channel"])
    if m_in["command"] == "stoprecord":
        stop_recording(m_in["channel"])
    if m_in["command"] == "startrecord":
        start_recording(m_in["channel"])
    if m_in["command"] == "stopplay":
        stop_playing(m_in["channel"])
    if m_in["command"] == "startplay":
        start_playing(m_in["channel"])

def stop_recording(channel):
    global stream_play
    global stream_record
    global record_running
    global record

    print("Stop Recording " +  channel)
    record_running = False

    stream_record = ""
    if stream_play != channel:
        mqtt.unsubscribe('hermes/audioServer/' + channel +'/audioFrame')        

    record.close()

def start_recording(channel):
    global stream_record
    global record_running
    record_running = False

    if stream_record != "":
        stop_recording(stream_record)

    print("Start Recording " +  channel)
    stream_record = channel
    mqtt.subscribe('hermes/audioServer/' + channel +'/audioFrame')

def stop_playing(channel):
    global stream_play
    global stream_record
    stream_play == ""
    if stream_record != channel:
        mqtt.unsubscribe('hermes/audioServer/' + channel +'/audioFrame')

def start_playing(channel):
    global stream_play

    stream_play = channel
    mqtt.subscribe('hermes/audioServer/' + channel +'/audioFrame')

def process_streamaudio(channel, msg, a_play, a_record):
    global record_running
    global record

    riff, size, fformat = struct.unpack('<4sI4s', msg.payload[:12])
    if riff != b'RIFF':
        print("RIFF parse error")
        return
    if fformat != b'WAVE':
        print("FORMAT parse error")
        return
    #print("size: %d" % size)

    # Data Header
    chunk_header = msg.payload[12:20]
    subchunkid, subchunksize = struct.unpack('<4sI', chunk_header)
    
    if (subchunkid == b'fmt '):
        aformat, channels, samplerate, byterate, blockalign, bps = struct.unpack('HHIIHH', msg.payload[20:36])
        bitrate = (samplerate * channels * bps) / 1024
    

    if a_record and not record_running :
        wfile = os.path.join(RECORD_PATH ,channel + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+".wav")
        print(" file : " +  wfile)

        record = wave.Wave_write
        record = wave.open(wfile, "wb")
        record.setnchannels(channels)
        record.setframerate(samplerate)
        record.setsampwidth(2)
        record_running = True

    chunkOffset = 52
    while (chunkOffset < size):
        subchunk2id, subchunk2size = struct.unpack('<4sI', msg.payload[chunkOffset:chunkOffset+8])
        chunkOffset += 8

        if (subchunk2id == b'data'):
            if a_record:
                record.writeframes(msg.payload[chunkOffset:chunkOffset+subchunk2size])
            if a_play:
                output_device1.write(msg.payload[chunkOffset:chunkOffset+subchunk2size])
        chunkOffset = chunkOffset + subchunk2size + 8


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
        doorbell_seeyou('',False)
    except:
        print("Unexpected error:", sys.exc_info()[0])
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    mqtt = mqtt.Client(SITE_ID)
    main()