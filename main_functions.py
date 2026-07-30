#sound
import sounddevice as sd
import soundfile as sf
import numpy as np
#stt
import whisper
#ollama
from ollama import chat
import json
import uuid
import os
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

class ollama:
    #because you have self, you need to call this function using ollama().ai(...)) instead of ollama.ai(...)
    def ai(self, chatid, message):
        msgs = self.handleInput(chatid, message)

        stream = chat(
            model='mistral',
            messages=msgs,
            stream=True,
        )

        for chunk in stream:
            yield chunk['message']['content']
            """
            #in the other file, you can do this:
            import main_functions as mf
            for text in mf.ollama().ai(False, "why is the sky blue?"):
                print(text, end='', flush=True)
            #this will take the stream and print it (but you should use text to speech)
            """

    def handleInput(self, chatid, message):
        if not os.path.isfile(f"./chats/{chatid}.json"):
            msgs = [{'role': 'user', 'content': message}]
            with open(f"./chats/{chatid}.json", "x") as file:
                json.dump(msgs, file, indent=4)
            return msgs
        else:
            with open(f"./chats/{chatid}.json", "r") as file:
                msgs = json.load(file)
            new_msg = {'role': 'user', 'content': message}
            msgs.append(new_msg)
            with open(f"./chats/{chatid}.json", "w"):
                json.dump(msgs, file, intent=4)
            return msgs

    #and this one, you need to call with ollama.delChat()
    def delChat(chatid):
        os.remove(f"./chats/{chatid}.json")

    def newId():
        return uuid.uuid4()
#this is for testing purposes
"""
file = "output.wav"
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

ollama().ai(ollama.newId(), "hello")
ollama.delChat("a046ec2a-f52c-43ef-903a-7b7ce8849ad7")
print(ollama.newId())
"""