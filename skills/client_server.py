from pymumble import Mumble, constants
import alsaaudio

class MumbleClient:
    def __init__(self, config):
        debug = int(config.get('debug')) == 1
        print('debug mumble')
        print(str(config.get('user')).replace('"', ''))
        self.mumble = Mumble(str(config.get('host')).replace('"', ''), str(config.get('user')).replace('"', ''), debug=debug)
        self.mumble.start()
        self.mumble.is_ready()

        self.mumble.set_receive_sound(True)
        self.mumble.users.myself.unmute()

        self.mumble.channels.find_by_name(str(config.get('channel')).replace('"', '')).move_in()
        self.mumble.set_bandwidth(int(config.get('bandwith')))

        self.mumble.callbacks.set_callback(
            constants.PYMUMBLE_CLBK_SOUNDRECEIVED, self.receive_sound)

        self.output_device1 = alsaaudio.PCM(
            alsaaudio.PCM_PLAYBACK, alsaaudio.PCM_NONBLOCK, str(config.get('audio_out')).replace('"', ''))
        self.output_device1.setchannels(int(config.get('channels')))
        self.output_device1.setrate(int(config.get('bitrate')))
        self.output_device1.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        self.output_device1.setperiodsize(int(config.get('periodsize')))
        
        # self.output_device2 = alsaaudio.PCM(
            # alsaaudio.PCM_PLAYBACK, alsaaudio.PCM_NONBLOCK, str(config.get('snips_in')).replace('"', ''))
        # self.output_device2.setchannels(int(config.get('channels')))
        # self.output_device2.setrate(int(config.get('bitrate')))
        # self.output_device2.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        # self.output_device2.setperiodsize(int(config.get('periodsize')))

        self.input_device1 = alsaaudio.PCM(
            alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK, str(config.get('audio_in')).replace('"', ''))
        self.input_device1.setchannels(int(config.get('channels')))
        self.input_device1.setrate(int(config.get('bitrate')))
        self.input_device1.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        self.input_device1.setperiodsize(int(config.get('periodsize')))

    def receive_sound(self, info, sound_chunk):
        self.output_device1.write(sound_chunk.pcm)

    def play_sound(self, sound_chunk):
        self.mumble.sound_output.add_sound(sound_chunk)

    def clear_input(self):
        self.input_device.read()

    def send_input_audio(self):

        length, data = self.input_device1.read()

        if length:
            self.play_sound(data)
            # self.output_device2.write(data)
