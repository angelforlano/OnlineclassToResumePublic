from utils import *

import time
import videoCleaner
import transcribe
import resume

makeDirIfNotExists("DONE/")
makeDirIfNotExists("TODO/")

todoFolder = "TODO/"
files = get_files(todoFolder)

for file in files:
    _filename = todoFolder+file
    st = time.time()
    _filename_raw = getFilename(file)

    _clips_folder = "DONE/"+_filename_raw+"/clips"
    _transcriptions_folder = "DONE/"+_filename_raw+"/transcription"
    _notes_folder = "DONE/"+_filename_raw+"/notes"
    _resumes_folder = "DONE/"+_filename_raw+"/resumes"

    makeDirIfNotExists("DONE/"+_filename_raw)
    #makeDirIfNotExists(_clips_folder)
    #makeDirIfNotExists(_notes_folder)
    #makeDirIfNotExists(_resumes_folder)
    makeDirIfNotExists(_transcriptions_folder)
    
    trancription = transcribe.audioToText(_filename, model_size="large")
    saveFile(_transcriptions_folder+"/transcription.txt", trancription)    

    #PART #3 Generate simples notes from file "all_transcription", for better resume results.
    #all_transcription_text = readFile(_transcriptions_folder+"/all_transcription.txt")
    #resume.transcripcionToNotes(all_transcription_text, "DONE/"+_filename_raw+"/notes")

    #PART #4 Generate IA resume from notes samples
    notes = get_files("DONE/"+_filename_raw+"/notes")

    all_summarized = ""
    for note in notes:
        resume_note = resume.generateResume(readFile(_notes_folder+"/"+note))
        _file_raw = note.split(".")[0]+"_summarized.txt"
        all_summarized += resume_note + "\n"
        saveFile(_resumes_folder+"/"+_file_raw, resume_note)
        time.sleep(3)
    saveFile(_resumes_folder+"/all_summarized.txt", all_summarized)

    et = time.time()
    
    #PART #5 delete original file from "TODO" list to avoid repeating process
    #os.remove(todoFolder+"/"+file)

    # get the execution time
    elapsed_time = round((et - st) / 60)
    print('Execution time:', elapsed_time, ' Minutes')