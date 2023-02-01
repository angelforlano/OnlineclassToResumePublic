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
        temperature = 0.3,
        max_tokens = 350,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0)

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
    return str(data)

audio_file = "La filosofía del estoicismo (TEST).mp4"

#audio_path = os.path.join(os.path.dirname(__file__), "DataManagemntEstanis/DM - Sesión 11 y 12.mp4")
audio_path = os.path.join(os.path.dirname(__file__), audio_file)

#generateResume(audioToText(audio_file, audio_path))

def transcripcionToNotes(_file_name, main_path):
    _file_name_raw = _file_name.split(".")[0]

    if not os.path.exists(main_path+"/notes"):
        os.makedirs(main_path+"/notes")

    _text = readFile(_file_name)

    WORDS_PER_PAGE = 750

    words = _text.split(" ")
    words_len = len(words)
    poins = _text.split(".")
    poins_len = len(poins)

    pages = round(words_len / WORDS_PER_PAGE)
    points_per_page = round(poins_len / pages)
    words_per_point = round(words_len / poins_len)

    print(pages)
    print(words_len)
    print(poins_len)
    print(points_per_page)
    print(words_per_point)

    """
    words_dictionry = {}
    for word in words:
        if not (word in words_dictionry):
            words_dictionry[word] = 1
        else:
            words_dictionry[word] = words_dictionry[word] +1
    words_frequency = dict(sorted(words_dictionry.items(), key=lambda item: item[1], reverse=True))
    print(words_frequency)"""

    for i in range(pages):
        _file = "part_" + str(i) + "_"  + str(pages-1)
        _text = ""
        for x in range(points_per_page):
            # print(len(poins))
            # print(x)
            if (len(poins) > x):
                _text += poins.pop(x)
                _text += "\n"
        
        with open('resumes/'+_file_name_raw+"/"+_file+".txt", 'w') as f:
            f.write(_text)

#saveResume(audio_file, generateResume(_text))

""" 
final_resume = ""
for filename in os.listdir('resumes/DM_Sesion_1_y_2_resume'):
    print(filename)
    final_resume = final_resume + readFile('resumes/DM_Sesion_1_y_2_resume/'+filename) + "\n"

#saveResume("DM_Sesion_1_y_2_resume.txt", final_resume)
#remove later "_resume.txt"
#saveResume(_filename+"_Resumed.text", generateResume(readFile("resumes/DM_Sesion_1_y_2/"+filename)))
#time.sleep(5)"""
