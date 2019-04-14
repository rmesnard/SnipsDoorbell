#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO

class RelaySwitch(object):

    def __init__(self, device_name, gpio_pin):
        self.name = device_name
        self._gpio_pin = gpio_pin
        self.gpio_init()

    def gpio_init(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._gpio_pin, GPIO.OUT)

        GPIO.output(self._gpio_pin, GPIO.LOW)
        self.__status = False

    def turn_on(self):
        self.__status = True
        GPIO.output(self._gpio_pin, GPIO.HIGH)
        print("[RelaySwitch] {} has been turned ON".format(self.name))

    def turn_off(self):
        self.__status = False
        GPIO.output(self._gpio_pin, GPIO.LOW)
        print("[RelaySwitch] {} has been turned OFF".format(self.name))

    def is_on(self):
        return self.__status

    def clear(self):
        GPIO.cleanup()