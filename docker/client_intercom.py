from pymumble import Mumble, constants
import alsaaudio

class MumbleClient:
    def __init__(self, config):
        debug = int(config['debug']) == 1
        self.mumble = Mumble(config['host'], config['user'], debug=debug)
        self.mumble.start()
        self.mumble.is_ready()

        self.mumble.set_receive_sound(True)
        self.mumble.users.myself.unmute()

        self.mumble.channels.find_by_name(config['channel']).move_in()
        self.mumble.set_bandwidth(int(config['bandwith']))

        self.mumble.callbacks.set_callback(
            constants.PYMUMBLE_CLBK_SOUNDRECEIVED, self.receive_sound)

        self.output_device1 = alsaaudio.PCM(
            alsaaudio.PCM_PLAYBACK, alsaaudio.PCM_NONBLOCK, config['output'])
        self.output_device1.setchannels(int(config['channels']))
        self.output_device1.setrate(int(config['bitrate']))
        self.output_device1.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        self.output_device1.setperiodsize(int(config['periodsize']))

        self.output_device2 = alsaaudio.PCM(
            alsaaudio.PCM_PLAYBACK, alsaaudio.PCM_NONBLOCK, config['snipsout'])
        self.output_device2.setchannels(int(config['channels']))
        self.output_device2.setrate(int(config['bitrate']))
        self.output_device2.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        self.output_device2.setperiodsize(int(config['periodsize']))
		
        self.input_device1 = alsaaudio.PCM(
            alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK, config['input'])
        self.input_device1.setchannels(int(config['channels']))
        self.input_device1.setrate(int(config['bitrate']))
        self.input_device1.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        self.input_device1.setperiodsize(int(config['periodsize']))

        self.input_device2 = alsaaudio.PCM(
            alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK, config['snipsin'])
        self.input_device2.setchannels(int(config['channels']))
        self.input_device2.setrate(int(config['bitrate']))
        self.input_device2.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        self.input_device2.setperiodsize(int(config['periodsize']))

    def send_audio_chunk(self, audio_chunk):
        self.output_device2.write(audio_chunk)
        self.mumble.sound_output.add_sound(audio_chunk)

    def receive_sound(self, info, sound_chunk):
        self.output_device1.write(sound_chunk.pcm)

    def play_sound(self, sound_chunk):
        self.output_device1.write(sound_chunk)

    def clear_input(self):
        self.input_device.read()

    def send_input_audio(self):
        length, data = self.input_device1.read()

        if length:
            self.send_audio_chunk(data)

        length, data = self.input_device2.read()

        if length:
            self.play_sound(data)
