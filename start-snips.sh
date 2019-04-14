#!/bin/bash
set -e

#verify that environment variables have been passed to this container. set the default value if not.
ENABLE_MQTT=${ENABLE_MQTT:-yes}
ENABLE_HOTWORD_SERVICE=${ENABLE_HOTWORD_SERVICE:-yes}


if [ ! -d "/usr/share/snips/voices" ]; then
	echo "Install mbrola voices:"
	ls /usr/share/snips/voices
	cp -f /usr/share/snips/voices/* /usr/lib/arm-linux-gnueabihf/espeak-data/voices/mb
fi

echo "Install config."
if [ ! -d "/usr/share/snips/config" ]; then
  mkdir /usr/share/snips/config
  cp -R /config /usr/share/snips
  chmod 777 /usr/share/snips/config
fi
echo "Install extra."
if [ ! -d "/usr/share/snips/extra" ]; then
  mkdir /usr/share/snips/extra
  cp -R /extra /usr/share/snips
  chmod 777 /usr/share/snips/extra
fi
echo "Install assistant."
if [ ! -d "/usr/share/snips/assistant" ]; then
  mkdir /usr/share/snips/assistant
  cp -R /assistant /usr/share/snips
  chmod 777 /usr/share/snips/assistant
fi

echo "Deploy assistant."

#deploy apps (skills). See: https://snips.gitbook.io/documentation/console/deploying-your-skills
snips-template render

#goto skill directory
cd /var/lib/snips/skills

#start with a clear skill directory
rm -rf *

if [ -e /usr/share/snips/assistant ]; then
	rm -f /etc/snips.toml
	cp -f /usr/share/snips/config/snips.toml /etc/snips.toml
fi

#download required skills from git
for url in $(awk '$1=="url:" {print $2}' /usr/share/snips/assistant/Snipsfile.yaml); do
	git clone $url
done

#be sure we are still in the skill directory
cd /var/lib/snips/skills

#run setup.sh for each skill.
find . -maxdepth 1 -type d -print0 | while IFS= read -r -d '' dir; do
	cd "$dir" 
	if [ -f setup.sh ]; then
		echo "Run setup.sh in "$dir
		#run the scrips always with bash
		bash ./setup.sh
	fi
	cd /var/lib/snips/skills
done

#skill deployment is done

echo "skill deployment is done"

#go back to root directory
cd /

#start own mqtt service.
if [ $ENABLE_MQTT == yes ]; then
	echo "Start mosquitto"
	mosquitto -d
fi

echo "Start snips services"

#start Snips analytics service
snips-analytics 2> /var/log/snips-analytics.log  &
snips_analytics_pid=$!

#start Snips' Automatic Speech Recognition service
snips-asr 2> /var/log/snips-asr.log &
snips_asr_pid=$!

#start Snips-dialogue service
snips-dialogue 2> /var/log/snips-dialogue.log  &
snips_dialogue_pid=$!

#start Snips hotword service

if [ $ENABLE_HOTWORD_SERVICE == yes ]; then
	snips-hotword 2> /var/log/snips-hotword.log & 
	snips_hotword_pid=$!
fi

#start Snips Natural Language Understanding service
snips-nlu 2> /var/log/snips-nlu.log &
snips_nlu_pid=$!

#start Snips Skill service
snips-skill-server 2> /var/log/snips-skill-server.log &
snips_skill_server_pid=$!

#start Snips TTS service
snips-tts 2> /var/log/snips-tts.log &
snips_tts_pid=$!

#start the snips audio server 
snips-audio-server --hijack localhost:64321 2> /var/log/snips-audio-server.log &
snips_audio_server_pid=$!

echo "snips services started.. check logs"

#run loopback
#modinfo snd-aloop
#modprobe snd-aloop	

echo "Start doorbell"
cd /usr/share/snips/extra
python3 doorbell.py

echo "all ok"

wait "$snips_analytics_pid" "$snips_asr_pid" "$snips_dialogue_pid" "$snips_hotword_pid" "$snips_nlu_pid" "$snips_skill_server_pid" "$snips_audio_server_pid"

