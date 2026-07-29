import sounddevice as sd
import soundfile as sf
import numpy as np

class sound:
    frames = []
    stream = None
    #recording level of the microfone should be 70%, or else it will sound odd
    #INPUT_GAIN = 0.7

    def record():
        global frames, stream
        frames = []
        stream = sd.InputStream(
            channels=1,
            samplerate=44100, 
            callback=lambda indata,
            *args: frames.append(indata.copy() * 0.7) # mic rec lvl
        )
        stream.start()

    def stop(filename):
        stream.stop()
        stream.close()
        sf.write(f"{filename}.wav", np.concatenate(frames), 44100)

    def play(file):
        audio_data, samplerate = sf.read(file)
        sd.play(audio_data, samplerate)
        sd.wait()

"""
#this is for testing purposes
input("press enter to start")
sound.record()
input ("press enter to end")
sound.stop('output')
input("press enter to play")
sound.play('output.wav')
"""