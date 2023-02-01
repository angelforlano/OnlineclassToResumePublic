import whisper

# transcribes the audio into text using the whisper AI model and saves it to a text file with the same name in the "transcribed" folder
def audioToText(audio_path, model_size = "small"):
    print("Transcribing > " + audio_path)
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path)
    return result["text"]