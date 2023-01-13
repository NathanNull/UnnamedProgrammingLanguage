from i_token import FuncDef, Var
import inspect, functools
import ptypes

# line 71

class PyVal: # haha duck typing go brr (sad isinstance noises)
    val = ""
    ops = {}
    props = {}
    
    def subclasses(self):
        return [type(self).__name__, "Value"]

class PyFunc(FuncDef):
    def __init__(self, name, params, func):
        self.name = name
        self.params = params
        self.func = func

    def __str__(self):
        return f"pyfunc {self.name} ({[p[0].name for p in self.params]})"

# class _pycls_inst_props(dict):
#     def __init__(self, inst):
#         self.inst = inst
#     def __getitem__(self, key):
#         return getattr(self.inst, key)
#     def __setitem__(self, key, val):
#         setattr(self.inst, key, val.val)
#     def __str__(self):
#         return f"(from {type(self.inst)})"

# class _pycls_class_props(dict):
#     def __init__(self, inst):
#         self.inst = inst
#     def __getitem__(self, key):
#         if key.startswith("__"):
#             raise KeyError("Magic methods are inaccessible")
#         return ptypes.to_val(getattr(self.inst, key))
#     def __setitem__(self, key, val):
#         setattr(self.inst, key, ptypes.from_val(val))
#     def __str__(self):
#         return f"(from {type(self.inst)})"

# class PyClass(PyVal):
#     def __init__(self, name, cls:type):
#         # need to pass in access to ClassInstance as I can't import
#         # it without infinite dependancy loop (feelsWeirdMan)
#         def constr(*args, cl_inst, existing_inst=None):
#             c = None if existing_inst is not None else cls(*args)
#             ci = cl_inst(self)
#             if c is None:
#                 props = _pycls_inst_props(existing_inst)
#                 ci.props = props
#             else:
#                 for pname in dir(c):
#                     if not pname.startswith("__"):
#                         attr = getattr(c, pname)
#                         ci.props[pname] = ptypes.to_val(attr)
#             return ci
#         self.constructor = constr
#         self.props = _pycls_class_props(cls)
#         self.cls = cls
#         self.val = name

#     def __str__(self):
#         return f"pyclass {self.val} {str({k:v for i,(k,v) in enumerate(self.props.items()) if i<7})[:-1]+', ...}'}"

#     def typestr(self):
#         return "py_class"

# the only thing that really matters
def from_python(func, name=None, static=False, convert_type=True):
    try:
        sig = inspect.signature(func)
        if name is None:
            name = func.__name__
        args = sig.parameters.keys()
    except ValueError:
        name = "builtin" if name is None else name
        args = []

    @functools.wraps(func)
    def wrapper(*args):
        if static:
            args = args[1:]
        if convert_type:
            args = [ptypes.from_val(a) for a in args]
        try:
            rtn = func(*args)
        except TypeError:
            print(static, args, func)
            raise
        return ptypes.to_val(rtn)

    pf = PyFunc(name, [[Var(a)] for a in args], wrapper)
    rf = ptypes.Func(name, pf, {})
    return rf

# class _pm_propdict(dict):
#     def __init__(self, module_name, module=None):
#         if module is None:
#             self.module = __import__(module_name).__dict__
#         else:
#             self.module = module.__dict__
#         self.cache = {}
#     def __getitem__(self, key):
#         if key in self.cache:
#             return self.cache[key]
#         itm = self.module[key]
#         if isinstance(itm, type):
#             # Means it is a class or something close to it
#             rtn = PyClass(key, itm)
#         elif isinstance(itm, type(inspect)):
#             rtn = PyModule(key, itm)
#         elif callable(itm):
#             # Means it is a function (ish)
#             rtn = from_python(itm, key)
#         else:
#             rtn = ptypes.to_val(itm)
#         self.cache[key] = rtn
#         return rtn
#     def __str__(self):
#         return str({k:v for i,(k,v) in enumerate(self.module.items()) if i<4})[:-1]+", ...}"

# class PyModule(PyVal):
#     def __init__(self, name, module=None):
#         self.val = name
#         self.props = _pm_propdict(name, module)
#         self.module = __import__(name) if module is None else module

#     def __str__(self):
#         return f"pymodule {self.val} with attrs {({k:v.out_str() for k, v in self.props.items()})}"

#     def typestr(self):
#         return "py_module"