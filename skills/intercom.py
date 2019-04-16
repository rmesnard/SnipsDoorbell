#!/usr/bin/env python3

from snipsTools import *
import time

from client_server import MumbleClient

class ListenMumble:

    def __init__(self):
        config = SnipsConfigParser.read_configuration_file('/usr/share/snips/config/snips.toml').get('mumble')
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
