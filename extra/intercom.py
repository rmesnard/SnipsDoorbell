#!/usr/bin/env python3

import configparser
import time

from client_server import MumbleClient

class ListenMumble:

    def __init__(self):
        config = configparser.ConfigParser()
        config.read('/usr/share/snips/config/snips.toml')
        self.mumble_client = MumbleClient(config['mumble'])
        self.exit = False


    def run(self):
        while not self.exit:
            self.mumble_client.send_input_audio()

if __name__ == '__main__':
    try:
        ListenMumble().run()
    except Exception as e:
        raise e
