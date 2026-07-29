import sounddevice as sd
import soundfile as sf
import numpy as np
import whisper

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
        sf.write(filename, np.concatenate(frames), 44100)

    playback_stream = None

    def play(file):
        global playback_stream
        audio_data, samplerate = sf.read(file)
        playback_stream = sd.play(audio_data, samplerate)

    def stop_play():
        global playback_stream
        sd.stop()

# stt = speech to text
# using openais whisper model
def stt(file):
    model = whisper.load_model("turbo")
    model = whisper.load_model("turbo")
    result = model.transcribe(file)
    #testing purposes
    #print(result["text"])
    return result["text"]

file = "output.wav"

"""
#this is for testing purposes

input("press enter to start")
sound.record()

input ("press enter to end")
sound.stop(file)

input("press enter to play")
sound.play(file)

input("press enter to stop playing")
sound.stop_play()

#before testing this, you need to uncomment the print(result[text]) line in the stt function
input("press enter to transcribe")
stt(file)

"""