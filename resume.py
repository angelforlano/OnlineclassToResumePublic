from utils import *
import os
import openai
import appsecrets
import time


# OpenAI
openai.api_key = appsecrets.OPENAI_KEY



def generateResume(text):
    _result = "no se puedo resumir!"
    
    try:
        #('Haz un resumen de una pagina aproximadamente del siguiente texto: "{0}"'.format(text))
        # Analizar el sentimiento de la review
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt = "Resumir: {0}".format(text),
            temperature = 0.3,
            max_tokens = 350,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0)

        _result = response["choices"][0]["text"]
    except Exception as e:
        print(e)
    
    return _result

def transcripcionToNotes(_text, main_path):
    WORDS_PER_PAGE = 700

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
        
        with open(main_path+"/"+_file+".txt", 'w') as f:
            f.write(_text)



if __name__ == "__main__":

    main_folder = "TODO/"

    folders = get_folders(main_folder)

    for folder in folders:
        all_transcription_file = main_folder+folder+"/transcription/all_transcription.txt"
        
        if not os.path.exists(all_transcription_file):
            print("all_transcription file not extist")
            transcriptions_files = get_files(main_folder+folder+"/transcription/")
            all_transcription = ""
            for file in transcriptions_files:
                all_transcription += readFile(main_folder+folder+"/transcription/"+file)
            saveFile(all_transcription_file, all_transcription)

        all_transcription_text = readFile(all_transcription_file)
        
        
        
        #Generates notes from all text.
        transcripcionToNotes(all_transcription_text, main_folder+folder+"/notes")

        notes = get_files(main_folder+folder+"/notes")

        all_summarized = ""
        for note in notes:
            resume = generateResume(readFile(main_folder+folder+"/notes/"+note))
            _file_raw = note.split(".")[0]+"_summarized.txt"
            all_summarized += resume
            all_summarized += "\n"
            saveFile(main_folder+folder+"/resumes/"+_file_raw, resume)
            time.sleep(3)
        saveFile(main_folder+folder+"/resumes/all_summarized.txt", all_summarized)