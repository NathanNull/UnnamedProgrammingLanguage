from errors import NotImplementedException
import pyfunc

# Need to detect classes that would be called 'getset_descriptor'
dt = __import__('datetime')
gsd = type(dt.datetime.day)

def to_val(pyval):
    if isinstance(pyval, Value):
        return pyval
    elif isinstance(pyval, int):
        return Int(pyval)
    elif isinstance(pyval, float):
        return Float(pyval)
    elif isinstance(pyval, bool):
        return Bool(pyval)
    elif isinstance(pyval, str):
        return String(pyval)
    elif isinstance(pyval, list):
        return Array([to_val(v) for v in pyval])
    elif type(pyval) == type:
        return pyfunc.PyClass(pyval.__name__, pyval)
    elif callable(pyval):
        static = "function" in type(pyval).__name__
        return pyfunc.from_python(pyval, static=static)
    elif isinstance(pyval, gsd):
        def pv_getattr(inst):
            return getattr(inst, pyval.__name__)
        return pyfunc.from_python(pv_getattr, pyval.__name__)
    elif pyval is None:
        return VNone(None)
    else:
        cls = to_val(type(pyval))
        return cls.constructor(cl_inst=ClassInstance, existing_inst=pyval)

def from_val(prval):
    if isinstance(prval, Array):
        return [from_val(p) for p in prval.val]
    elif isinstance(prval, pyfunc.PyClass):
        return prval.cls
    elif isinstance(prval, pyfunc.PyModule):
        return prval.module
    else:
        return prval.val

class Value:
    def __init__(self, val):
        try:
            assert type(self.val) == type(val)
        except AssertionError as e:
            raise ValueError(f"{type(val)} recieved when expected {type(self.val)}") from e
        self.val = val
    
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
                        return self.ops[op][t_str](self, other)
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
        }
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
        "length": lambda me: Int(len(me.val))
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
        "reversed": pyfunc.from_python(lambda self: Array(list(reversed(self.val))), "reversed"),
        "reverse": pyfunc.from_python(lambda self: self.val.reverse(), "reverse")
    }

    def __str__(self):
        return str([str(v) for v in self.val])

    def out_str(self):
        return "["+", ".join(itm.out_str() for itm in self.val)+"]"

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

    def __init__(self, name, props, constructor, subs, ctx):
        self.constructor = constructor
        if constructor is None:
            self.constructor = pyfunc.from_python(lambda: ClassInstance(self), name, True)
        self.ctx = Ctx(ctx)
        self.subs = subs

        self.props = {}
        if subs:
            for cls in subs:
                for name,prop in cls.props.items():
                    self.props[name] = prop
        for name, prop in props.items():
            self.props[name] = prop
                
        super().__init__(name)

    def __str__(self):
        return f"class {self.val}"
    
    def out_str(self):
        return str(self)

class ClassInstance(Value):
    val = ""
    
    def __init__(self, class_: Class):
        super().__init__(class_.val)
        self.class_ = class_
        self.props = class_.props

    @property
    def is_builtin(self):
        # if props isn't a dict, it's that mapping of
        # an object's properties from pyfunc, so it's
        # builtin
        return type(self.props) != dict

    def __str__(self):
        input(self.class_)
        if self.is_builtin:
            return "pyci of "+str(self.props.inst)
        else:
            return f"        instance {self.val}"
    
    def out_str(self):
        return str(self)

    def typestr(self):
        if self.is_builtin:
            return type(self.props.inst).__name__
        return super().typestr()