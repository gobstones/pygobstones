import os

def read_file(fn):
    f = open(fn, 'r')
    c = f.read()
    f.close()
    return c

# Clothing

def clothing_dir_for_file(filepath):
        return os.path.join(os.path.dirname(str(filepath)), 'Vestimentas')

def clothing_for_file_exists(filepath):
    return os.path.exists(clothing_dir_for_file(str(filepath)))
