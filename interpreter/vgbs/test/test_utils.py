import importlib
import re
import os
import sys
import subprocess

def delete_files_in_dir(dir, exceptions=[]):
    for f in os.listdir(dir):
        if not f in exceptions:
            os.remove(os.path.join(dir, f))

def group(lst, n):
    res = []
    sublst = []
    for x in lst:
      sublst.append(x)
      if len(sublst) == n:
          res.append(sublst)
          sublst = []
    if len(sublst) > 0:
        res.append(sublst)
    return res

def flatten(lst):
    res = []
    for x in lst:
        if isinstance(x, list):
            res.extend(flatten(x))
        else:
            res.append(x)
    return res

def parent_dir(f):
    return os.path.split(os.path.realpath(f))[0]

def module_dir(obj):
    return os.path.split(sys.modules[obj.__module__].__file__)[0]

def dir_has_tests(dir):
    for fn in os.listdir(os.path.join(parent_dir(__file__), dir)):
        if "test" in fn:
            return True
    return False

def is_module(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except Exception as e:
        return False

def run_cmd(cmd):
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

def append_file(fn, s):
    f = open(fn, "a")
    f.write(s)
    f.close

def read_file(fn):
    f = open(fn, 'r')
    s = f.read()
    f.close()
    return s

def read_file_lines(fn):
    f = open(fn, 'r')
    ls = f.readlines()
    f.close
    return ls

def first_half(lst): return lst[:len(lst) / 2]
def second_half(lst): return lst[len(lst) / 2:]

def all_permutations(xs):
  if xs == []:
    yield []
  else:
    for i in range(len(xs)): 
      for p in all_permutations(xs[:i] + xs[i + 1:]):
        yield [xs[i]] + p

def all_subsets(xs):
  if xs == []:
    yield []
  else:
    for s in all_subsets(xs[1:]):
      yield s
      yield [xs[0]] + s

def all_slicings(xs):
  if len(xs) == 0:
    yield []
  elif len(xs) == 1:
    yield [xs]
  else:
    for s in all_slicings(xs[1:]):
      yield [[xs[0]]] + s
      yield [[xs[0]] + s[0]] + s[1:]