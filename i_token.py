# A token that represents a part of a line for the interpreter
class InterpreterToken:
    pass

class Section(InterpreterToken):
    def __init__(self, inner_tokens):
        self.inner_tokens = inner_tokens

    def __str__(self):
        return "sl-["+", ".join(str(t) for t in self.inner_tokens)+"]"

class MultilineSection(InterpreterToken):
    def __init__(self, lines):
        self.lines = lines

    def i_str(self, itm):
        if isinstance(itm, list):
            return str([self.i_str(i) for i in itm])
        return str(itm)
        
    def __str__(self):
        istr = "\n\t".join("\n".join(self.i_str(t) for t in self.lines).split("\n"))
        return "ml-{\n\t"+istr+"\n}"

class Tuple(InterpreterToken):
    def __init__(self, vals):
        self.vals = [v for v in vals if v]

    def itm_str(self, itm):
        if isinstance(itm, list):
            return " ".join(str(t) for t in itm)
        return str(itm)

    def __str__(self):
        return "t-["+", ".join(self.itm_str(t) for t in self.vals)+"]"

class BinaryOperator(InterpreterToken):
    def __init__(self, lhs, op, rhs):
        self.lhs = lhs
        self.rhs = rhs
        self.op = op

    def __str__(self):
        return f"({self.lhs} b{self.op} {self.rhs})"

class UnaryOperator(InterpreterToken):
    def __init__(self, op, rhs):
        self.rhs = rhs
        self.op = op

    def __str__(self):
        return f"(u{self.op} {self.rhs})"

class Var(InterpreterToken):
    def __init__(self, name):
        self.name = name
        
    def __str__(self):
        return self.name

class Keyword(InterpreterToken):
    def __init__(self, kw):
        self.kw = kw

    def __str__(self):
        return self.kw

keywords = {name: Keyword(name) for name in [
    "if", "else", "while", "func",
    "return", "import", "class",
    "for", "in"
]}

class FuncCall(InterpreterToken):
    def __init__(self, target, fname, params):
        self.target = target
        self.fname = fname
        self.params = params

    def __str__(self):
        fname = self.fname
        if self.target is not None:
            fname = str(self.target) + "." + fname
        return f"{fname} ({[[str(i) for i in v] for v in self.params.vals]})"

class Return(InterpreterToken):
    def __init__(self, stmt):
        self.stmt = stmt

    def __str__(self):
        return f"return-{self.stmt}"

class ArrayLiteral(InterpreterToken):
    def __init__(self, vals):
        self.vals = vals

    def itm_str(self, itm):
        if isinstance(itm, list):
            return " ".join(str(t) for t in itm)
        return str(itm)

    def __str__(self):
        return "arr-["+", ".join(self.itm_str(t) for t in self.vals)+"]"

class ArrIdx(InterpreterToken):
    def __init__(self, var, idx_stmt):
        self.var = var
        self.idx_stmt = idx_stmt

    def __str__(self):
        return f"(index [{self.idx_stmt}] of {self.var})"

class GetProperty(InterpreterToken):
    def __init__(self, target, prop):
        self.target = target
        self.prop = prop

    def __str__(self):
        return f"{self.target}.{self.prop}({type(self.prop).__name__})"

class Import(InterpreterToken):
    def __init__(self, module_name):
        self.module_name = module_name

    def __str__(self):
        return f"import {self.module_name}"
    
# A token representing a line of code
class LineToken(InterpreterToken):
    pass

class Assignment(LineToken):
    def __init__(self, target, var, stmt, idx=None):
        self.target = target
        self.var = var
        self.stmt = stmt
        self.idx = idx

    def __str__(self):
        targetvar = str(self.var) if self.var is not None else ""
        if self.idx is not None:
            targetvar = f"{targetvar}[{self.idx}]"
        if self.target is not None:
            targetvar = f"{self.target}.{targetvar}"
        return f"{targetvar} set-to {self.stmt}"

class CompoundAssignment(LineToken):
    def __init__(self, target, var, op, stmt, idx=None):
        self.target = target
        self.var = var
        self.op = op
        self.stmt = stmt
        self.idx = idx

    def __str__(self):
        targetvar = str(self.var) if self.var is not None else ""
        if self.idx is not None:
            targetvar = f"{targetvar}[{self.idx}]"
        if self.target is not None:
            targetvar = f"{self.target}.{targetvar}"
        return f"{targetvar} {self.op}= {self.stmt}"

class AcceptsSection(LineToken):
    section = None

class IfStatement(AcceptsSection):
    def __init__(self, check):
        self.check = check

    def __str__(self):
        return f"if-({self.check[0]}) {self.section}"

class ElseStatement(AcceptsSection):
    def __str__(self):
        return f"else {self.section}"

class WhileLoop(AcceptsSection):
    def __init__(self, check):
        self.check = check

    def __str__(self):
        return f"while-({self.check[0]}) {self.section}"

class ForLoop(AcceptsSection):
    def __init__(self, var, loop):
        self.var = var
        self.loop = loop

    def __str__(self):
        return f"for-({self.var} {self.loop}) {self.section}"

class FuncDef(AcceptsSection):
    def __init__(self, name, params):
        self.name = name
        self.params = params

    def __str__(self):
        params_str = ""
        if self.params and self.params[0]: # If it has any params
            params_str = str([p[0].name for p in self.params])
        return f"func {self.name} ({params_str}) {self.section}"

class ClassDef(AcceptsSection):
    def __init__(self, name, subs):
        self.name = name
        self.subs = subs

    def __str__(self):
        return f"classdef {self.name} {self.section}"