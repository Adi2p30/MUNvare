import os
import numpy as np
import sounddevice as sd
import torch
import whisper
import wavio
import ssl
import threading
from scipy.io.wavfile import write

ssl._create_default_https_context = ssl._create_unverified_context

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("base")  

def record_speech(filename="temp_speech.wav", samplerate=16000):
    stop_recording = threading.Event()

    def record_audio():
        print("Recording started...")
        audio_data = []  
        with sd.InputStream(samplerate=samplerate, channels=1, dtype='int16') as stream:
            print("Recording... Speak now.")
            while not stop_recording.is_set():  
                audio_chunk, overflowed = stream.read(samplerate * 5)
                audio_data.append(audio_chunk)
        
        full_audio = np.concatenate(audio_data, axis=0)
        write(filename, samplerate, full_audio)
        print(f"Recording stopped and saved as {filename}.")
    
    command = input("Enter command (start): ").strip().lower()
    if command == "start":
        recording_thread = threading.Thread(target=record_audio)
        recording_thread.start()

        input("Press Enter to stop recording...")
        stop_recording.set()
        recording_thread.join()
        transcription = transcribe_audio(filename, task="transcribe", language="english")
        return transcription
    else:
        print("Invalid command. Please type 'start' to begin recording.")

def transcribe_audio(filename="temp_speech.wav", task="transcribe", language="english"):
    audio = whisper.load_audio(filename)
    audio = whisper.pad_or_trim(audio)
    mel = whisper.log_mel_spectrogram(audio).to(model.device)

    options = whisper.DecodingOptions(language=language, task=task, without_timestamps=True)
    result = model.decode(mel, options)
    return result.text


