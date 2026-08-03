#general purpose
import json, uuid, os
#sound
import sounddevice as sd
import soundfile as sf
import numpy as np
#stt
import whisper
#ai
from ollama import chat
#tts
from piper import PiperVoice
from langdetect import detect as ld
import wave

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

    def stop():
        stream.stop()
        stream.close()
        fileId = newId()
        sf.write(f"audio/stt/{fileId}.wav", np.concatenate(frames), 44100)
        return fileId

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
                for text in mf.ai().ollama(mf.newId(), "why is the sky blue?"):
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

def tts(text):
    # Load a voice model
    language = ld(text)

    with open("audio/tts/voices/tts_models.json", "r") as file:
        langlist = json.load(file)
        lang_model = None
        for i in langlist:
            if i["language"] == language:
                lang_model = i["model_dir"]
                break
    
    if not lang_model:
        raise ValueError(f"Keine Voice für language='{language}' gefunden")

    if not os.path.isfile(lang_model):
        raise FileNotFoundError(f"Modell-ONNX existiert nicht: {lang_model}")

    print("Using language:", language)
    print("Using model:", lang_model)

    voice = PiperVoice.load(
        model_path=lang_model,
        config_path=f"{lang_model}.json",
        use_cuda=False  # Set to True for GPU acceleration
    )

    out_wav = f"audio/tts/audio/{newId()}.wav"
    open(out_wav, "x")
    with wave.open(out_wav, "wb") as wav_file:
        # Synthesize speech
        voice.synthesize_wav(
            text=text,
            wav_file=wav_file,
        )
    
    return wav_file



"""
ttsEngine = pyttsx3.init()
ttsEngine.setProperty('rate', 140)

def tts(text):
    ttsEngine.say(text)
    ttsEngine.runAndWait()

"""
audiofile = tts("Dans deux semaines, je vais aller dans les vacances. Je suis tres heureuse. Je veux aller a la piscine.")
