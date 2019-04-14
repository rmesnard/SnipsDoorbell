FROM raspbian/stretch

#Change the timezone to your current timezone!!
ENV TZ=Europe/PARIS

RUN set -x && \ 
	ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

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

RUN cd /opt && pip3 install configparser pyalsaaudio protobuf

COPY ./config/ /config/ 
COPY ./extra/ /extra/ 
COPY ./assistant/ /assistant/ 
COPY mbrola /usr/bin/mbrola 
COPY ./voices/ /usr/share/mbrola/


#RUN modinfo snd-aloop
#RUN modprobe snd-aloop	
	
RUN set -x && \
	pip3 install virtualenv

#Is this really required? 
RUN set -x && \	
	usermod -aG snips-skills-admin root
	
COPY start-snips.sh start-snips.sh

EXPOSE 1833/tcp


CMD ["bash","/start-snips.sh"]
