import os
from os.path import expanduser

def read_file(fn):
    f = open(fn, 'r')
    c = f.read()
    f.close()
    return c

def path_join(*list):
    path = ""
    for p in list:
        path += os.path.join(path, p)
    return path

def root_path():
    return os.path.dirname(os.path.dirname(__file__))

def user_path():
    return expanduser("~")

# Clothing

def clothing_dir_for_file(filepath):
        return os.path.join(os.path.dirname(str(filepath)), 'Vestimentas')

def clothing_for_file_exists(filepath):
    return os.path.exists(clothing_dir_for_file(str(filepath)))    