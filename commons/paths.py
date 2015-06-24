import os
from os.path import expanduser

def path_join(*path_parts):
    path = ""
    for p in path_parts:
        path += os.path.join(path, p)
    return path

def root_path():
    return os.path.dirname(os.path.dirname(__file__))

def user_path():
    return expanduser("~")

def gobstones_folder():
    return os.path.join(user_path(), "gobstones")

last_location = gobstones_folder()