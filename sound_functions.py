#this file is for 
#   recording or playing audio files
#   text to speech
#   speech to text

#general purpose
import json, uuid, os, subprocess, shutil
#sound
import sounddevice as sd
import soundfile as sf
import numpy as np
#stt
import whisper
#tts
from piper import PiperVoice
from langdetect import detect as ld
import wave

class sound:
    frames = []
    stream = None

    if not os.path.isdir("audio/stt/"):
        os.mkdir("audio/stt/")

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
        audio_data, samplerate = sf.read(file, dtype="float32")
        playback_stream = sd.play(audio_data, samplerate, blocking=False)

    def stop_play():
        sd.stop()

# stt = speech to text
# using openais whisper model
def stt(file):
    model = whisper.load_model("turbo")
    model = whisper.load_model("turbo")
    result = model.transcribe(file)
    os.remove(file)
    return result["text"]

def newId():
    return uuid.uuid4()

def tts(text):
    model_paths = "audio/tts/voices/"

    # Load a voice model
    language = ld(text)

    with open("audio/tts/tts_models.json", "r") as file:
        langlist = json.load(file)
        lang_model = None
        for i in langlist:
            if i["language"] == language:
                lang_model = i["model_dir"]
                lang_link = i["model_link"]
                break
    
    if not lang_model:
        raise ValueError(f"no vioce found for language='{language}'")    
    tts_model_check(language, lang_model, lang_link)

    voice = PiperVoice.load(
        model_path=f"{model_paths}{language}/{lang_model}",
        config_path=f"{model_paths}{language}/{lang_model}.json",
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
    
    return out_wav

#this functions checks whether the corresponding error is there and if not, it downloads it.
def tts_model_check(language, lang_model, lang_link):
    model_paths = "audio/tts/voices/"
 
    if not os.path.isdir(model_paths):
        os.mkdir(model_paths)
  
    if not os.path.isdir(f"{model_paths}{language}/"):
        os.mkdir(f"{model_paths}{language}/")

    if not os.path.isfile(f"{model_paths}{language}/{lang_model}"):
        subprocess.run(["wget", lang_link])
        shutil.move(lang_model, f"{model_paths}{language}/")

    if not os.path.isfile(f"{model_paths}{language}/{lang_model}.json"):
        subprocess.run(["wget", f"{lang_link}.json"])
        shutil.move(f"{lang_model}.json", f"{model_paths}{language}/")

    print("Using language:", language)
    print("Using model:", lang_model)


