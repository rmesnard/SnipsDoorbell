# SnipsServer-Docker

install git

sudo apt-get install git

Build

sudo docker build -t rmesnard/snips-server github.com/rmesnard/SnipsServer-Docker


docker volume create snips_config
docker volume create snips_log

docker run -d -p 192.168.2.105:445:445 \
  -v  snips_config:/share/data \
  -v  snips_log:/share/log \
  --name samba trnape/rpi-samba \
  -u "admin:hapwd" \
  -s "snips_config:/share/data:rw:admin" \
  -s "snips_log:/share/log:rw:admin" 


Run

sudo docker run -d --name snips-server -v snips_log:/var/log -v snips_config:/usr/share/snips --device=/dev/snd:/dev/snd -e ENABLE_MQTT=no -e ENABLE_HOTWORD_SERVICE=yes -p 1883:1883 rmesnard/snips-server



docker run -d --restart always \
    --name restreamer \
    -e "RS_USERNAME=admin" -e "RS_PASSWORD=hapwd" -e "RS_MODE=RASPICAM" \
    -p 8080:8080 \
    -v /mnt/restreamer/db:/restreamer/db \
    -v /opt/vc:/opt/vc \
    --privileged \
    datarhei/restreamer-armv7l:latest

console

	
docker exec -it snips-server bash