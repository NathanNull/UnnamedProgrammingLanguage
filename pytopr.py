from pyfunc import from_python
from ptypes import Value, Func, to_val, Module
from errors import ProgramRuntimeError

def make_importable(pymod):
    try:
        fns = pymod.functions
    except:
        fns = []
        
    try:
        vars = pymod.variables
    except:
        vars = {}

    if not (vars or fns):
        raise ProgramRuntimeError(f"{pymod.__name__} isn't a valid module")

    prglob = {}
    for fn in fns:
        if isinstance(fn, Func):
            prglob[fn.func.name] = fn
        else:
            prglob[fn.__name__] = from_python(fn)
    for name, var in vars.items():
        if isinstance(var, Value):
            prglob[name] = var
        else:
            prglob[name] = to_val(var)

    return Module(pymod.__name__, prglob)