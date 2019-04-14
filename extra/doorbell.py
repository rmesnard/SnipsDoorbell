import configparser
import time

from client_server import MumbleClient

class ListenMumble:

    def __init__(self):
        config = configparser.ConfigParser()
        config.read('doorbell.ini')
        self.mumble_client = MumbleClient(config['doorbell'])
        self.exit = False


    def run(self):
        while not self.exit:
            self.mumble_client.send_input_audio()

if __name__ == '__main__':
    try:
        ListenMumble().run()
    except Exception as e:
        raise e
