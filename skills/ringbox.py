#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import functools


class RingBox(object):
    def __init__(self, mqtt_addr, site_id, relay, sht31, pir):

        self.__site_id = site_id
        self.__relay = relay
        self.__sht31 = sht31
		self.__pir = pir

        self.__mqtt_addr = mqtt_addr

    def handler_servicename(self, hermes, intent_message):
        print("Relay servicename On")
        #self.__relay.turn_on()
        hermes.publish_end_session(
            intent_message.session_id,
            self.__i18n.get('relayTurnOn')
        )

    def handler_getmessage(self, hermes, intent_message):
        print("left a message")
        #self.__relay.turn_off()
        hermes.publish_end_session(
            intent_message.session_id,
            self.__i18n.get('relayTurnOff')
        )

    def handler_sayyes(self, hermes, intent_message):
        print("answer yes")
        #humidity = self.__sht31.get_humidity_string()
        hermes.publish_end_session(
            intent_message.session_id,
            self.__i18n.get('checkHumidity', {"humidity": humidity})
        )

    def handler_sayno(self, hermes, intent_message):
        print("answer no")
        #temperature = self.__sht31.get_temperature_string()
        hermes.publish_end_session(
            intent_message.session_id,
            self.__i18n.get('checkTemperature', {"temperature": temperature})
        )

    def run(self):
        with Hermes(self.__mqtt_addr) as h:
            h.subscribe_intent(
                'servicename',
                self.handler_servicename
            ) \
             .subscribe_intent(
                'getmessage',
                self.handler_getmessage
            ) \
             .subscribe_intent(
                'sayyes',
                self.handler_sayyes
            ) \
             .subscribe_intent(
                'sayno',
                self.handler_sayno
            ) \
             .start()