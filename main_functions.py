#sound
import sounddevice as sd
import soundfile as sf
import numpy as np
#stt
import whisper
#ai
from ollama import chat
import json, uuid, os
#tts
import pyttsx3

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

class ai:
    #because you have self, you need to call this function using ollama().ai(...)) instead of ollama.ai(...)
    def ollama(self, chatid, message):
        msgs = self.jsonAppend(chatid, 'user', message)

        stream = chat(
            model='mistral',
            messages=msgs,
            stream=True,
        )
        
        answer = ""

        for chunk in stream:
            text = chunk['message']['content']
            answer += text
            yield text
            """
                #in the other file, you can do this:
                import main_functions as mf
                for text in mf.ai().ollama(mf.ai.newId(), "why is the sky blue?"):
                    print(text, end='', flush=True)
                #this will take the stream and print it (but you should use text to speech)
            """

        self.jsonAppend(chatid, 'assistant', answer)

    def jsonAppend(self, id, usr, msg):
        if usr not in ("user", "assistant"):
            print("!!! The user must be either 'user' or 'assistant'")
            return 
    
        path = f"./chats/{id}.json"
        newmsg = {'role': usr, 'content': msg}
        content = []

        if not os.path.isfile(path):    
            with open(path, "x") as file:
                content = [newmsg]
                json.dump(content, file, indent=4)
        else:
            with open(path, "r") as file:
                content = json.load(file)
            content.append(newmsg)

            with open(path, "w") as file:
                json.dump(content, file, indent=4)
        return content

    #and this one, you need to call with ollama.delChat()
    def delChat(chatid):
        os.remove(f"./chats/{chatid}.json")

    def newId():
        return uuid.uuid4()

ttsEngine = pyttsx3.init()
ttsEngine.setProperty('rate', 140)

def tts(text):
    ttsEngine.say(text)
    ttsEngine.runAndWait()
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

ai().ollama(ai.newId(), "hello")
ai.delChat("a046ec2a-f52c-43ef-903a-7b7ce8849ad7")
print(ai.newId())

testid = ai.newId()
answer = ''
for t in ai().ollama(testid, "hello"):
    answer += t
tts(answer)
print()
for t in ai().ollama(testid, "why is the sky blue?"):
    print(t, end='', flush=True)
"""
