# SNIPS Doorbell

Doorbell that integrate a SNIPS voice assistant to say welcome and record messages from visitor when you are not at home.

# HacksterIo

This project is available at [HacksterIO] (https://www.hackster.io/remy-mesnard/doorbell-intercom-with-snips-voice-assistant-68e77a)

#The Idea
Building a Doorbell including a voice assisstant to reply to visitor. The doorbell is able to speak with visitor ( using TTS ) and run voice command.
Connected to Home Automation system , the doorbell know if you are at home or not. Base on this information , the doorbell can :

    Say a welcome message with TTS. 
    Ring inside the house and wait that somebody reply to visitor thru the Intercom functionality.
    Ask the visitor if he want to record a message for you or try to join you by phone.
    Try to identify the visitor by keywords "postal service" , "UPS" .


SnipsDrawing.jpg

#Software
The voice assistant use the SNIPS platform. You can design your own voice interactions by creating an assistant on their website, then upload this assisstant to your hardware. SNIPS work offline on your local network. No cloud. connection.
The intercom functionality is managed by MUMBLE platform. Mumble is an open source voice chat system that run on many OS. 
Communication between systems use the MQTT protocol. This protocol can be use also to interact with Home Automation software HomeAssistant 

#Hardware
We need 2 units to start.  1 Satellite inside the doorbell and 1 Base Server in the house.
Both are based on Raspberry Pi platform. 

    The Satellite , you can use the Snips Voice Interaction Base Kit  or build your own satellite by assembling together : RaspberryPi Zero + ReSpeaker 2 Mics Pi Hat You need to connect a pushbuton to the GPIO of the RPI.
    The Base server, require only one RaspberryPi 3B to run the basic voice assistant doorbell.

For the Intercom capabilities, you can add :

    a ReSpeaker 2 Mics Pi Hat to your Base server and a push button connected to GPIO.
    or a second satelite inside house. This satelite can be use also for home automation interface.
    or use an Android / Windows / Linux tablet  
    or use your smartphone 

#Step 0 - MQTT (optional)
MQTT protocol is used by SNIPS and HomeAssistant. Both provide their own Broker. But you can also use a separate broker like mosquito. Here's the way to setup your own MQTT Broker
...
#Step 1 - SNIPS Base server
To build the Base , you need a raspberry Pi 3 or equivalent running with armbian distribution. I use the xxxx image. After a classic installation ( setup network, enable SSH .. ) proceed to SNIPS installation :
...
If you use the embedded MQTT broker of HomeAssistant :
If you use the embedded MQTT broker of SNIPS:
#Step 2 - Mumble 
A mumble server (murmur) is used to manage the voice communication between visitor and users. Mumble is a multi platform open source software. Here we use mumur on RaspBerry pi , but you can install your Mumble server on other device / OS following the guide in the wiki. 
...
#Step 3 - Home Assistant 
Home Assistant is used as home automation system in this project. But you can replace it by other system that support MQTT protocol.
...
If you use the embedded MQTT broker of HomeAssistant :
If you use the embedded MQTT broker of SNIPS:
#Step 4 - SNIPS Doorbell Satellite 
This part need more than software parts. Here we must build the doorbell itself with Audio functionality and a push button.
Using Seed Studio Snips Voice Interaction Kit  :

    Follow the kit assembling guide
    Replace the temperature sensor by a push button.

Using Raspberry Pi 3 or Zero with Respeaker 2Mic  :

    Setup your raspberry pi with Respeaker 2Mic pi Hat
    Plug an external speaker
    Connect a Push Button to the Respeaker 2Mic pi Hat

-- freezing diagram --
Using Raspberry Pi 3 or Zero with USB Sound Card
Install SNIPS Satellite software.
Install python Mumble client
Setup Audio
...
#Step 5 - SNIPS at Home Satellite  (optional)
...
#Step 6 - SmartPhone configuration  (optional)
...

# Links
- [pymumble](https://github.com/azlux/pymumble)
- [pyalsaaudio](http://larsimmisch.github.io/pyalsaaudio)
- [RPi.GPIO](https://pypi.python.org/pypi/RPi.GPIO)
