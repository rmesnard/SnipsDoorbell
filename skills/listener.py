#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import json
import struct
import wave
import datetime
import os
import sys
import alsaaudio

from snipsTools import *

VERSION = '1.0.0'

config = SnipsConfigParser.read_configuration_file('/usr/share/snips/config/snips.toml')
config_common = config.get('snips-common')
config_audio = config.get('snips-audio-player')

MQTT_ADDR = str(config_common.get('mqtt')).replace('"', '')
SITE_ID = str(config_common.get('site_id')).replace('"', '')

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


def on_connect(client, userdata, flags, rc):
	print('Connected to MQTT system')
	mqtt.subscribe('snips/audioClient/' + SITE_ID )

def on_message(client, userdata, msg):
    global stream_play
    global stream_record
    #print('msg.topic ' + msg.topic)
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

#    if stream_play != "":
#        stop_playing(stream_play)

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

    mqtt_parse = MQTT_ADDR.split(":")
    print("connectint to : "+ MQTT_ADDR)

    mqtt.on_connect = on_connect
    mqtt.on_message = on_message

    mqtt.connect(str(mqtt_parse[0]), int(mqtt_parse[1]))

    mqtt.loop_forever()        

if __name__ == "__main__":
	mqtt = mqtt.Client(SITE_ID)
	main()