#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO

class GpioInput(object):

    def __init__(self, device_name, gpio_pin):
        self.name = device_name
        self._gpio_pin = gpio_pin
        self.gpio_init()

    def gpio_init(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._gpio_pin, GPIO.IN)

        if GPIO.input(channel):
            self.__status = True
        else:
            self.__status = False

    def is_on(self):
        if GPIO.input(channel):
            self.__status = True
        else:
            self.__status = False

        return self.__status
