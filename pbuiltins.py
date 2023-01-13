from ptypes import String, Int, Float, Dict
from pyfunc import from_python
from random import randint
from time import sleep
from replit import clear
from collections.abc import Iterable
from errors import InvalidValueType, ProgramRuntimeError
from sys import stdout

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

def pr_print(obj, end='\n'):
    if not isinstance(end, str):
        end = tostring(end).val
    print(tostring(obj).val, end=end)
    stdout.flush()

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

def pr_abs(num):
    if isinstance(num, int):
        return Int(abs(num))
    elif isinstance(num, float):
        return Float(abs(num))
    raise InvalidValueType('arg for abs must be a number')

def pr_pow(base, exp):
    try:
        res = pow(base, exp)
    except:
        raise InvalidValueType('arg for abs must be a number')
    if isinstance(res, int):
        return Int(res)
    else:
        return Float(res)

def pr_enum(arr):
    return [list(l) for l in enumerate(arr)]
    
def pr_zip(*arrs):
    return [list(l) for l in zip(*arrs)]

def error(info):
    raise ProgramRuntimeError(info)

def dictionary(kvps):
    d = Dict({k:v for k,v in kvps})
    return d

functions = [
    # screen I/O
    from_python(pr_print, "print", convert_type=False),
    input,

    # generators
    from_python(pr_range, "range"),
    randint,

    # converters
    from_python(tostring, convert_type=False),
    from_python(lambda s: int(s), "toint"),
    from_python(typestr, convert_type=False),
    bin,

    # array checks/transforms
    all, any,
    from_python(pr_enum, 'enumerate'),
    dictionary, zip,
    sum, max, min,

    # file I/O
    readfile,
    writefile,
    appendfile,

    # math
    from_python(pr_abs, 'abs'),
    from_python(pr_pow, 'pow'),

    # utils
    clear,
    sleep,
]