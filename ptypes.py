from errors import NotImplementedException
import pyfunc, interpreter

def to_val(pyval):
    if isinstance(pyval, Value):
        return pyval
    elif isinstance(pyval, bool):
        # apparently isinstance(True, int)
        # returns True, so we need to check
        # for bool first
        return Bool(pyval)
    elif isinstance(pyval, int):
        return Int(pyval)
    elif isinstance(pyval, float):
        return Float(pyval)
    elif isinstance(pyval, str):
        return String(pyval)
    elif isinstance(pyval, list):
        return Array([to_val(v) for v in pyval])
    elif isinstance(pyval, dict):
        return Dict({to_val(k):to_val(v) for k,v in pyval.items()})
    # elif type(pyval) == type:
    #     return pyfunc.PyClass(pyval.__name__, pyval)
    # elif callable(pyval):
    #     static = "function" in type(pyval).__name__
    #     return pyfunc.from_python(pyval, static=static)
    # elif isinstance(pyval, gsd):
    #     def pv_getattr(inst):
    #         return getattr(inst, pyval.__name__)
    #     return pyfunc.from_python(pv_getattr, pyval.__name__)
    elif pyval is None:
        return VNone(None)
    # else:
    #     cls = to_val(type(pyval))
    #     return cls.constructor(cl_inst=ClassInstance, existing_inst=pyval)

def from_val(prval):
    if isinstance(prval, Array):
        return [from_val(p) for p in prval.val]
    # elif isinstance(prval, pyfunc.PyClass):
    #     return prval.cls
    # elif isinstance(prval, pyfunc.PyModule):
    #     return prval.module
    elif isinstance(prval, Func):
        itpr = interpreter.active_interpreter[-1]
        return lambda *args: itpr.run_fn_raw(
            prval.func, [to_val(a) for a in args], itpr.globals)
    else:
        return prval.val

class Value:
    def __init__(self, val):
        try:
            assert type(self.val) == type(val)
        except AssertionError as e:
            raise ValueError(
                f"{type(val)} recieved when expected {type(self.val)}") from e
        self.val = val
        if not isinstance(self, Func):
            self.props.update({
                'dir': pyfunc.from_python(
                    lambda me: Dict(me.props), 'dir', convert_type=False)
            })
    
    val=None

    def subclasses(self):
        return [c.__name__ for c in type(self).__mro__[:-1]]

    ops = {}

    props = {}

    def op_allowed(self, other_name, op):
        if op not in self.ops:
            return
        op_dict = self.ops[op]
        op_types = ",".join(op_dict.keys()).split(",")
        return other_name in op_types
    
    def op(self, other, op):
        sbc = other.subclasses()
        for subclass in sbc:
            if self.op_allowed(subclass, op):
                for t_str in self.ops[op].keys():
                    if subclass in t_str.split(","):
                        if callable(self.ops[op][t_str]):
                            return self.ops[op][t_str](self, other)
                        else:
                            fn = self.ops[op][t_str]
                            return interpreter.active_interpreter[-1].run_fn_raw(
                               fn.func, [self, other], fn.ctx
                            )
        print(op)
        print(self, other)
        raise NotImplementedException(
            f"Operator {op} not defined between {type(self)} and {type(other)}"
        )

    def uop(self, op):
        if self.op_allowed('__unary__', op):
            return self.ops[op]['__unary__'](self) 

    def out_str(self):
        return str(self.val)

    def typestr(self):
        return self.__class__.__name__

class Ctx(dict):
    def __init__(self, parent=None):
        self.parent = parent
    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            if self.parent is None:
                print("Parent is none")
                print(self)
                raise
            return self.parent[key]
    def __str__(self):
        sstr = super().__str__()
        pstr = str(self.parent)
        return f"{sstr} (parent={pstr})"

class Module(Value):
    val = ""
    ops = {}
    props = {}

    def __init__(self, name, globals):
        super().__init__(name)
        self.props = globals

    def __str__(self):
        return f"module {self.val} with attrs {({k:v.out_str() for k, v in self.props.items()})}"

    def out_str(self):
        return str(self)

class Func(Value):
    val = ""
    ops = {}
    props = {}

    def __init__(self, name, func, ctx):
        super().__init__(name)
        self.func = func
        self.params = func.params
        self.ctx = Ctx(ctx)

    def __str__(self):
        return f"func {self.val}"

    def out_str(self):
        return str(self)

    @property
    def builtin(self):
        return isinstance(self.func, pyfunc.PyFunc)

class VNone(Value):
    val=None

    def __str__(self):
        return "Nothing"

class Int(Value):
    val=0

    ops = {
        "+": {
            "Int,Float": lambda me, other: type(other)(me.val+other.val)
        },
        "-": {
            "Int,Float": lambda me, other: type(other)(me.val-other.val),
            "__unary__": lambda me: Int(-me.val)
        },
        "*": {
            "Int,Float,String": lambda me, other: type(other)(me.val*other.val)
        },
        "/": {
            "Int,Float": lambda me, other: Float(me.val/other.val)
        },
        "<": {
            "Int,Float": lambda me, other: Bool(me.val<other.val)
        },
        ">": {
            "Int,Float": lambda me, other: Bool(me.val>other.val)
        },
        "<=": {
            "Int,Float": lambda me, other: Bool(me.val<=other.val)
        },
        ">=": {
            "Int,Float": lambda me, other: Bool(me.val>=other.val)
        },
        "==": {
            "Int,Float": lambda me, other: Bool(me.val==other.val)
        },
        "!=": {
            "Int,Float": lambda me, other: Bool(me.val!=other.val)
        },
        "&": {
            "Int": lambda me, other: Int(me.val&other.val)
        },
        "|": {
            "Int": lambda me, other: Int(me.val|other.val)
        },
        "^": {
            "Int": lambda me, other: Int(me.val^other.val)
        },
        ">>": {
            "Int": lambda me, other: Int(me.val>>other.val)
        },
        "<<": {
            "Int": lambda me, other: Int(me.val<<other.val)
        },
    }

    def __str__(self):
        return "I "+str(self.val)

    def out_str(self):
        return str(self.val)

class Float(Value):
    val=0.0

    ops = {
        "+": {
            "Int,Float": lambda me, other: Float(me.val+other.val)
        },
        "-": {
            "Int,Float": lambda me, other: Float(me.val-other.val),
            "__unary__": lambda me: Int(-me.val)
        },
        "*": {
            "Int,Float": lambda me, other: Float(me.val*other.val)
        },
        "/": {
            "Int,Float": lambda me, other: Float(me.val/other.val)
        },
        "<": {
            "Int,Float": lambda me, other: Bool(me.val<other.val)
        },
        ">": {
            "Int,Float": lambda me, other: Bool(me.val>other.val)
        },
        "<=": {
            "Int,Float": lambda me, other: Bool(me.val<=other.val)
        },
        ">=": {
            "Int,Float": lambda me, other: Bool(me.val>=other.val)
        },
        "==": {
            "Int,Float": lambda me, other: Bool(me.val==other.val)
        },
        "!=": {
            "Int,Float": lambda me, other: Bool(me.val!=other.val)
        }
    }

    props = {
        'round': pyfunc.from_python(lambda me: round(me), 'round')
    }

    def __str__(self):
        return "F "+str(self.val)
    
class String(Value):
    val=""

    ops = {
        "+": {
            "String": lambda me, other: String(me.val+other.val)
        },
        "==": {
            "String": lambda me, other: Bool(me.val==other.val)
        },
        "!=": {
            "String": lambda me, other: Bool(me.val!=other.val)
        }
    }

    props = {
        "length": pyfunc.from_python(
            lambda me: len(me), 'length'),
        "startswith": pyfunc.from_python(
            lambda me, prefix: me.startswith(prefix), 'startswith'),
        "endswith": pyfunc.from_python(
            lambda me, suffix: me.endswith(suffix), 'endswith'),
        "lower": pyfunc.from_python(
            lambda me: me.lower(), 'lower'),
        "upper": pyfunc.from_python(
            lambda me: me.upper(), 'upper'),
        "strip": pyfunc.from_python(
            lambda me: me.strip(), 'strip'),
        "split": pyfunc.from_python(
            lambda me, sep: me.split(sep), 'split')
    }

    def __str__(self):
        return "S \""+self.val+"\""

class Bool(Value):
    val=False

    ops = {
        "==": {
            "Bool": lambda me, other: Bool(me.val==other.val)
        },
        "!=": {
            "Bool": lambda me, other: Bool(me.val!=other.val)
        },
        "||": {
            "Bool": lambda me, other: Bool(me.val or other.val)
        },
        "&&": {
            "Bool": lambda me, other: Bool(me.val and other.val)
        },
        "!": {
            "__unary__": lambda me: Bool(not me.val)
        }
    }

    def __str__(self):
        return "B "+str(self.val).lower()

    def out_str(self):
        return str(self.val).lower()

class Array(Value):
    val = []

    ops = {
        "+": {
            "Value": lambda me, other: Array(me.val+[other])
        }
    }

    props = {
        "length": lambda me: Int(len(me.val)),
        "reversed": pyfunc.from_python(
            lambda self: list(reversed(self)), "reversed"),
        "reverse": pyfunc.from_python(lambda self: self.val.reverse(), "reverse"),
        "map": pyfunc.from_python(
            lambda self, func: [func(itm) for itm in self], "map"),
        "ele": pyfunc.from_python(lambda self, idx: self[idx], "ele"),
        "filter": pyfunc.from_python(
            lambda self, func: [itm for itm in self if func(itm)], "filter"),
        "has": pyfunc.from_python(lambda self, key: key in self, "has"),
        "join": pyfunc.from_python(lambda me, joiner: joiner.join(me), 'join'),
        "sort": pyfunc.from_python(lambda me: me.sort(), 'sort'),
        "slice": pyfunc.from_python(lambda me, start, end: me[slice(start, end)])
    }

    def __str__(self):
        return str([str(v) for v in self.val])

    def out_str(self):
        return "["+", ".join(itm.out_str() for itm in self.val)+"]"

def rm_key(d, key):
    del d[key]

class Dict(Value):
    val = {}
    ops = {}
    
    props = {
        "length": pyfunc.from_python(lambda self: len(self), 'length'),
        "ele": pyfunc.from_python(lambda self, idx: self[idx], "ele"),
        "has": pyfunc.from_python(lambda self, key: key in self, "has"),
        "hasval": pyfunc.from_python(
            lambda self, val: val in self.values(), "hasval"),
        "remove": pyfunc.from_python(rm_key, 'remove'),
        "keys": pyfunc.from_python(lambda self: list(self.keys()), 'keys'),
        "values": pyfunc.from_python(lambda self: list(self.values()), 'values'),
        "items": pyfunc.from_python(
            lambda self: [list(i) for i in self.items()], 'items'),
    }

    def __str__(self):
        return '{'+', '.join(f"{k}: {v}" for k,v in self.val.items())+'}'

    def out_str(self):
        return '{'+', '.join(f"{k}: {v.out_str()}" for k,v in self.val.items())+'}'

class Context(Value):
    val = ""
    ops = {}
    props = {}

    def __init__(self, ctx):
        self.props = ctx

    def __str__(self):
        return "Context: "+str(self.props)

    def out_str(self):
        return str(self)

class Class(Value):
    val = ""
    ops = {}
    props = {}

    def __init__(self, cname, ops, props, constructor, subs, ctx):
        self.constructor = constructor
        if constructor is None:
            self.constructor = pyfunc.from_python(lambda: ClassInstance(self), cname, True)
        self.ctx = Ctx(ctx)
        self.subs = subs

        self.props = {}
        if subs:
            for cls in subs:
                for name,prop in cls.props.items():
                    self.props[name] = prop
        for name, prop in props.items():
            self.props[name] = prop

        for name, op in ops.items():
            self.ops[name] = op
                
        super().__init__(cname)

    def __str__(self):
        return f"class {self.val}"
    
    def out_str(self):
        return str(self)

class ClassInstance(Value):
    val = ""
    
    def __init__(self, class_: Class):
        super().__init__(class_.val)
        self.class_ = class_
        self.props = Ctx(class_.props)
        self.ops = class_.ops

    # Some code that was used during the testing phase
    # for the python imports. I don't need it anymore,
    # since I'm not doing that. Too frustrating.
    # @property
    # def is_builtin(self):
    #     # if props isn't a dict, it's that mapping of
    #     # an object's properties from pyfunc, so it's
    #     # builtin
    #     return type(self.props) != dict

    def __str__(self):
        # if self.is_builtin:
        #     return "pyci of "+str(self.props.inst)
        # else:
        props = {k:v.out_str() for k,v in self.props.items()}
        return f"classinst {self.val} with props {props}"
    
    def out_str(self):
        return str(self)

    def typestr(self):
        if self.is_builtin:
            return type(self.props.inst).__name__
        return super().typestr()