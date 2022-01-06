from talon.lib import cubeb
import threading
import functools
import wave
import struct

"""Module for playing wav files in Talon.

Only works with 16-bit signed wavs. Not designed to work with spamming.

Author: Ryan Hileman (lunixbochs).
Modified by GitHub user Jcaw, and again by Github user chaosparrot.
""" 

class _WavSource:
    def __init__(self, path, volume=1): 
        self.path = path
        try:
            wav_file = wave.open(path)
            self.params = wav_file.getparams()
            if self.params.sampwidth != 2:
                raise Exception("only 16-bit signed PCM supported")
            nframes = self.params.nframes
            frames = wav_file.readframes(nframes)
            self.samples = struct.unpack(
                "<{}h".format(nframes * self.params.nchannels), frames
            )
            self.samplerate = self.params.framerate
            self.channels = self.params.nchannels
            if self.channels == 2:
                self.samples = self.samples[::2]
                self.channels = 1
            
            # Adjust the volume of this source
            volume_adjusted_samples = []
            for sample in self.samples:
                volume_adjusted_samples.append(int(sample * volume))
            self.samples = volume_adjusted_samples
            
        finally:
            wav_file.close()

class _Player:
    def __init__(self, rate, fmt, channels):
        self.lock = threading.Lock()
        self.ctx = cubeb.Context()
        params = cubeb.StreamParams(rate=rate, format=fmt, channels=channels)
        self.buffer = []
        self.stream = self.ctx.new_output_stream(
            "player", None, params, latency=-1, data_cb=self._source
        )
        self.stream.start()

    def _source(self, stream, samples_in, samples_out):
        needed = len(samples_out)
        with self.lock:
            if len(self.buffer) > 0:
                frame = self.buffer[:needed]
                if len(frame) < needed:
                    frame += [0] * (needed - len(frame))
                samples_out[:] = frame
                self.buffer = self.buffer[needed:]
                return needed
        return needed

    def append(self, samples):
        with self.lock:
            self.buffer += samples
            
    def clear(self):
        with self.lock:
            self.buffer = []
            
# Cache to avoid repeated, slow disk I/O
@functools.lru_cache(maxsize=32)
def load_wav(path, volume=1):
    return _WavSource(path, volume)

_players = {}

def clear_audio():
    player_key = (44100, 1)
    player = _players.get(player_key)
    if player:
        player.clear()

def play_wav(path, volume=1):
    global _players
    wav = load_wav(path, volume)
    # Player seems to leak. Creating many players eventually causes audio to
    # corrupt. We can re-use old players to prevent it.
    #
    # NOTE this will play identically sampled wavs one by one, but differently
    # sampled wavs in parallel.
    #
    # TODO: Allow multiple wavs to be played at once without corrupting.
    player_key = (wav.samplerate, wav.channels)
    player = _players.get(player_key)
    if not player:
        player = _Player(wav.samplerate, cubeb.SampleFormat.S16LE, wav.channels)
        _players[player_key] = player
    player.append(wav.samples)
    return player