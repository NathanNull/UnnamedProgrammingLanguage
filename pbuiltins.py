from ptypes import String
from pyfunc import from_python
from random import randint
from time import sleep
from replit import clear
from collections.abc import Iterable

def tostring(obj):
    if isinstance(obj, Iterable) and not isinstance(obj, str):
        str = "["+", ".join(str(t) for t in obj)+"]"
    elif hasattr(obj, 'out_str'):
        str = obj.out_str()
    else:
        str = obj
    return String(str)

def typestr(obj):
    if hasattr(obj, 'typestr'):
        return String(obj.typestr())
    return String(str(type(obj).__name__))

def pr_print(obj):
    if isinstance(obj, Iterable) and not isinstance(obj, str):
        print("["+", ".join(str(t) for t in obj)+"]")
    elif hasattr(obj, 'out_str'):
        print(obj.out_str())
    else:
        print(obj)

def readfile(fname):
    with open(fname) as file:
        data = file.read()
    return data

def writefile(fname, data):
    with open(fname, 'w') as file:
        file.write(data)

def appendfile(fname, data):
    with open(fname, 'a') as file:
        file.write(data)

def pr_range(max):
    return list(range(max))

# IMPORTANT: might need to make these static
builtins = {
    "print": from_python(pr_print, "print", convert_type=False),
    "tostring": from_python(tostring, convert_type=False),
    "input": from_python(input),
    "range": from_python(pr_range, "range"),
    "randint": from_python(randint),
    "sleep": from_python(sleep),
    "typestr": from_python(typestr, convert_type=False),
    "clear": from_python(clear),
    "toint": from_python(lambda s: int(s), "toint"),
    "readfile": from_python(readfile),
    "writefile": from_python(writefile),
    "appendfile": from_python(appendfile),
}