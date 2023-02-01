import whisper
import os
import openai
import appsecrets

# OpenAI
openai.api_key = appsecrets.OPENAI_KEY

def generateResume(text):
    _pront = "What are 5 key points I should know when studying Ancient Rome?"
    
    #('Haz un resumen de una pagina aproximadamente del siguiente texto: "{0}"'.format(text))
    # Analizar el sentimiento de la review
    response = openai.Completion.create(
        engine="text-davinci-003",
        #1 pagina aproximadamente
        prompt = "Resumir: {0}".format(text),
        temperature = 0.7,
        max_tokens = 350,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
        )

    print(response)

    return response["choices"][0]["text"]

def saveResume(file, resume):
    with open('resumes/'+file+"_resume.txt", 'w') as f:
        f.write(resume)
    
    return resume

# transcribes the audio into text using the whisper AI model and saves it to a text file with the same name in the "transcribed" folder
def audioToText(audio_file_name, audio_path, model_size = "small"):
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path)

    file_name = audio_file_name.split(".")
    file_name = file_name[0]

    with open('transcribed/'+file_name+"_transcribed.txt", 'w') as f:
        f.write(result["text"])
    
    return result["text"]

def readFile(filename):
    with open(filename, 'r') as file:
        data = file.read().replace('\n', '')
    
    return data

audio_file = "DM_Sesion_5_y_6"

audio_path = os.path.join(os.path.dirname(__file__), "DataManagemntEstanis/DM - Sesión 5 y 6.mp4")

audioToText(audio_file, audio_path)