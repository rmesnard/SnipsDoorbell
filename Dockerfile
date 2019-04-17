FROM raspbian/stretch

RUN set -x && \
	apt-get update && apt-get dist-upgrade -y
 
RUN set -x && \	
	apt-get install -y dirmngr apt-transport-https apt-utils

RUN set -x && \
	bash -c  'echo "deb https://raspbian.snips.ai/stretch stable main" > /etc/apt/sources.list.d/snips.list'

RUN set -x && \
	apt-key adv --keyserver gpg.mozilla.org --recv-keys D4F50CDCA10A2849

RUN set -x && \
	apt-get update	
	
#since recommended packets are NOT installed by default, we have to install them explicit
RUN set -x && \
	apt-get install -y snips-makers-tts alsa-utils snips-platform-voice snips-skill-server mosquitto snips-analytics snips-asr snips-audio-server snips-dialogue snips-hotword snips-nlu curl unzip snips-template python3-pip python3-setuptools python3-wheel libasound2-dev libasound2 libasound2-data git espeak
	
#python libraries

RUN cd /opt && pip3 install configparser pyalsaaudio protobuf RPi.GPIO smbus2 hermes-python paho-mqtt
	
RUN set -x && \
	pip3 install virtualenv

#Is this really required? 
RUN set -x && \	
	usermod -aG snips-skills-admin root

COPY ./config/ /config/ 
COPY ./assistant/ /assistant/ 
COPY ./skills/ /skills/ 
COPY mbrola mbrola

COPY start-snips.sh start-snips.sh

EXPOSE 1833/tcp

CMD ["bash","/start-snips.sh"]
