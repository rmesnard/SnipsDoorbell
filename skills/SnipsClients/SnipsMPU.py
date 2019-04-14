#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import functools

from hermes_python.hermes import Hermes
from hermes_python.ontology import *

class SnipsMPU(object):
    def __init__(self, i18n, mqtt_addr, site_id, relay, sht31):
        self.THRESHOLD_INTENT_CONFSCORE_DROP = 0.3
        self.THRESHOLD_INTENT_CONFSCORE_TAKE = 0.6

        self.__i18n = i18n
        self.__site_id = site_id
        self.__relay = relay
        self.__sht31 = sht31

        self.__mqtt_addr = mqtt_addr

    def check_site_id(handler):
        @functools.wraps(handler)
        def wrapper(self, hermes, intent_message):
            if intent_message.site_id != self.__site_id:
                return None
            else:
                return handler(self, hermes, intent_message)
        return wrapper

    def check_confidence_score(handler):
        @functools.wraps(handler)
        def wrapper(self, hermes, intent_message):
            if handler is None:
                return None
            if intent_message.intent.confidence_score < self.THRESHOLD_INTENT_CONFSCORE_DROP:
                hermes.publish_end_session(
                    intent_message.session_id,
                    ''
                )
                return None
            elif intent_message.intent.confidence_score <= self.THRESHOLD_INTENT_CONFSCORE_TAKE:
                hermes.publish_end_session(
                    intent_message.session_id,
                    self.__i18n.get('error.doNotUnderstand')
                )
                return None
            return handler(self, hermes, intent_message)
        return wrapper

    @check_confidence_score
    @check_site_id
    def handler_relay_turn_on(self, hermes, intent_message):
        print("Relay Turn On")
        self.__relay.turn_on()
        hermes.publish_end_session(
            intent_message.session_id,
            self.__i18n.get('relayTurnOn')
        )

    @check_confidence_score
    @check_site_id
    def handler_relay_turn_off(self, hermes, intent_message):
        print("Relay Turn Off")
        self.__relay.turn_off()
        hermes.publish_end_session(
            intent_message.session_id,
            self.__i18n.get('relayTurnOff')
        )

    @check_confidence_score
    @check_site_id
    def handler_check_humidity(self, hermes, intent_message):
        print("Humidity Check")
        humidity = self.__sht31.get_humidity_string()
        hermes.publish_end_session(
            intent_message.session_id,
            self.__i18n.get('checkHumidity', {"humidity": humidity})
        )

    @check_confidence_score
    @check_site_id
    def handler_check_temperature(self, hermes, intent_message):
        print("Temperature Check")
        temperature = self.__sht31.get_temperature_string()
        hermes.publish_end_session(
            intent_message.session_id,
            self.__i18n.get('checkTemperature', {"temperature": temperature})
        )

    def start_block(self):
        with Hermes(self.__mqtt_addr) as h:
            h.subscribe_intent(
                'relayTurnOn',
                self.handler_relay_turn_on
            ) \
             .subscribe_intent(
                'relayTurnOff',
                self.handler_relay_turn_off
            ) \
             .subscribe_intent(
                'checkHumidity',
                self.handler_check_humidity
            ) \
             .subscribe_intent(
                'checkTemperature',
                self.handler_check_temperature
            ) \
             .start()