#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from snipsTools import *
from RelaySwitch import RelaySwitch
from SHT31 import SHT31
from SnipsClients import SnipsMPU

VERSION = '0.3.0'

CONFIG_INI = 'config.ini'
I18N_DIR = 'assets/i18n'

config = SnipsConfigParser.read_configuration_file(CONFIG_INI).get('global')

MQTT_ADDR_HOST = str(config.get('mqtt_host'))
MQTT_ADDR_PORT = str(config.get('mqtt_port'))
MQTT_ADDR = "{}:{}".format(MQTT_ADDR_HOST, MQTT_ADDR_PORT)
SITE_ID = str(config.get('site_id'))
RELAY_GPIO = int(config.get('relay_gpio_bcm'))
TEMP_UNIT = str(config.get('temperature_unit'))
LOCALE = str(config.get('locale'))

i18n = SnipsI18n(I18N_DIR, LOCALE)
relay = RelaySwitch.RelaySwitch('screen', RELAY_GPIO)
sht31 = SHT31.SHT31(TEMP_UNIT)
client = SnipsMPU.SnipsMPU(i18n, MQTT_ADDR, SITE_ID, relay, sht31)

if __name__ == "__main__":
    try:
        client.start_block()

    except KeyboardInterrupt:
        relay.clear()