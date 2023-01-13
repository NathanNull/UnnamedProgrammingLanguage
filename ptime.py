import time

def gmtime(t=None):
    return list(time.gmtime(t))

def localtime(t=None):
    return list(time.localtime(t))

def asctime(t=None):
    if t is None:
        t = time.localtime()
    return time.asctime(tuple(t))

functions = [
    time.ctime,
    time.time,
    time.time_ns,
    gmtime,
    localtime,
    asctime
]