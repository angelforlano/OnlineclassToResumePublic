import os

def get_folders(path):
    _folders = os.listdir(path)
    for file in _folders:
        if (os.path.isfile(os.path.join(path, file))):
            _folders.pop(file)
    return _folders

def get_files(path):
    _folders = os.listdir(path)
    for file in _folders:
        if not (os.path.isfile(os.path.join(path, file))):
            _folders.pop(file)
    return _folders

def readFile(filename):
    with open(filename, 'r') as file:
        data = file.read().replace('\n', '')
    return str(data)

def saveFile(file, text):
    with open(file, 'w') as f:
        f.write(text)
    return text

def makeDirIfNotExists(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)
        return True
    return False

def getFilename(filename:str):
    return filename.split(".")[0]