from i_token import BinaryOperator, Section,\
    Assignment, CompoundAssignment,\
    Var, IfStatement, WhileLoop, FuncDef,\
    FuncCall, Return, ArrayLiteral, GetProperty,\
    ElseStatement, Import, ClassDef, ArrIdx, ForLoop,\
    UnaryOperator
from errors import ProgramSyntaxError, InvalidValueType,\
    Expected, ImportError
from ptypes import Value, Bool, Array, VNone, Module,\
    Func, Class, ClassInstance, Context, Ctx, to_val
from pbuiltins import builtins
from pyfunc import PyFunc, PyModule, PyClass

from lexer import Lexer
from parser import Parser

import config
import sys

class Interpreter:
    def __init__(self):
        self.globals = Ctx()
        for k, v in builtins.items():
            self.globals[k] = v
        self.last_line = (None, True)
        self.this_module = Module("__main__", self.globals)

    def run_fn(self, func, args, ctx, target, construct = False):
        if construct:
            rfunc = target.class_.constructor
            if isinstance(rfunc, type(lambda x:x)):
                # yeah idrk what else to do here
                rf = rfunc
                f = lambda *args: rf(*args[1:], cl_inst=ClassInstance)
                real_func = PyFunc(func, ([Var('arg')] for _ in range(50)), f)
            else:
                real_func = rfunc.func
        elif isinstance(target.props[func], Func):
            rfunc = target.props[func]
            real_func = rfunc.func
        else:
            ci = ClassInstance(target.props[func])
            self.run_fn(func, args, ctx, ci, construct=True)
            return ci

        val_args = [target] + [self.run_stmt(a[0], ctx) for a in args.vals if a]
        if any(isinstance(target, cls) for cls in (Module, PyModule, Context)):
            val_args.pop(0)

        f_ctx = Ctx(rfunc.ctx)
        for a, name in zip(val_args, real_func.params):
            f_ctx[name[0].name] = a

        if isinstance(real_func, PyFunc):
            rtn = real_func.func(*val_args)
        else:
            rtn = self.run(real_func.section.lines, f_ctx)

        return rtn
    
    def run_stmt(self, i_token, ctx):
        curr_tk = i_token
        while not (isinstance(curr_tk, Value) or type(curr_tk) in [PyClass, PyModule]):
            if isinstance(curr_tk, Var):
                curr_tk = ctx[curr_tk.name]
            elif isinstance(curr_tk, FuncCall):
                target = Context(ctx) if curr_tk.target is None\
                    else self.run_stmt(curr_tk.target, ctx)
                curr_tk = self.run_fn(curr_tk.fname, curr_tk.params, ctx, target)
            elif isinstance(curr_tk, Section):
                curr_tk = self.run_stmt(curr_tk.inner_tokens[0], ctx)
            elif isinstance(curr_tk, BinaryOperator):
                lhs = self.run_stmt(curr_tk.lhs, ctx)
                rhs = self.run_stmt(curr_tk.rhs, ctx)
                curr_tk = lhs.op(rhs, curr_tk.op)
            elif isinstance(curr_tk, UnaryOperator):
                rhs = self.run_stmt(curr_tk.rhs, ctx)
                curr_tk = rhs.uop(curr_tk.op)
            elif isinstance(curr_tk, ArrayLiteral):
                elements = [self.run_stmt(v, ctx) for v in curr_tk.vals if v]
                curr_tk = Array(elements)
            elif isinstance(curr_tk, ArrIdx):
                target = self.run_stmt(curr_tk.var, ctx)
                idxs = []
                for v in curr_tk.idx_stmt.vals:
                    idxs.append(self.run_stmt(v, ctx))
                if len(idxs) == 1:
                    curr_tk = target.val[idxs[0].val]
                else:
                    curr_tk = Array([target.val[idx.val] for idx in idxs])
            elif isinstance(curr_tk, GetProperty):
                target = self.run_stmt(curr_tk.target, ctx)
                curr_tk = target.props[curr_tk.prop]
                if callable(curr_tk):
                    # This is for python-determined values
                    # sort of like @property does.
                    if not (hasattr(target, 'is_builtin') and target.is_builtin):
                        curr_tk = curr_tk(target)
                    else:
                        curr_tk = curr_tk()
                        curr_tk = to_val(curr_tk)
                elif not hasattr(curr_tk, "val"):
                    # Not a terrible way of checking
                    # if a value is a python one or a
                    # custom one
                    curr_tk = to_val(curr_tk)
            else:
                print(type(curr_tk))
                raise ProgramSyntaxError(f"Unsure what to do with this {curr_tk}<-{i_token}")
        return curr_tk

    def run_line(self, line, ctx):
        ran = True
        if isinstance(line, Assignment):
            target = ctx if line.target is None\
                else self.run_stmt(line.target, ctx).props
            rtnval = self.run_stmt(line.stmt, ctx)
            if line.idx is None:
                target[line.var] = rtnval
            elif line.var is None:
                def find_target(t):
                    if isinstance(t, Var):
                        return self.run_stmt(t, ctx)
                    elif isinstance(t, ArrIdx):
                        return find_target(t.var).val[self.run_stmt(t.idx_stmt, ctx).val[0].val]
                idx = self.run_stmt(line.idx, ctx)
                find_target(line.target).val[idx.val[0].val] = rtnval
            else:
                idx = self.run_stmt(line.idx, ctx)
                target[line.var].val[idx.val[0].val] = rtnval
        elif isinstance(line, CompoundAssignment):
            if line.target is not None:
                target = self.run_stmt(line.target, ctx)
            else:
                target = Context(ctx)
            stmt_val = self.run_stmt(line.stmt, ctx)
            if line.idx is None:
                rtnval = target.props[line.var].op(stmt_val, line.op)
                target.props[line.var] = rtnval
            else:
                idx = self.run_stmt(line.idx, ctx)
                rtnval = target.val[idx.val[0].val].op(stmt_val, line.op)
                target.val[idx.val[0].val] = rtnval
        elif isinstance(line, IfStatement):
            val = self.run_stmt(line.check[0], ctx)
            if not isinstance(val, Bool):
                raise InvalidValueType(f"The statement {line.check} can't be used in an if statement as it returns the non-boolean value {val}")
            elif val.val:
                rtn = self.run(line.section.lines, ctx)
                self.last_line = (line, True)
                return rtn
            else:
                ran = False

                
        elif isinstance(line, WhileLoop):
            val = self.run_stmt(line.check[0], ctx)
            ran = False
            while isinstance(val, Bool) and val.val:
                ran = True
                self.last_line = (None, True)
                rtn = self.run(line.section.lines, ctx)
                if not isinstance(rtn, VNone):
                    return rtn
                val = self.run_stmt(line.check[0], ctx)
            if not isinstance(val, Bool):
                raise InvalidValueType(f"The statement {line.check} can't be used in a while loop as it returns the non-boolean value {val}")


        elif isinstance(line, ForLoop):
            loop = self.run_stmt(line.loop, ctx)
            assert isinstance(loop, Array)
            ran = False
            for itm in loop.val:
                ctx[line.var] = itm
                self.last_line = (None, True)
                rtn = self.run(line.section.lines, ctx)
                if not isinstance(rtn, VNone):
                    return rtn
                
        elif isinstance(line, ElseStatement):
            if type(self.last_line[0]) not in [IfStatement, WhileLoop, ForLoop]:
                raise Expected(f"Expected if or while statement before else (got {self.last_line[0]})")
            if not self.last_line[1]:
                rtn = self.run(line.section.lines, ctx)
                return rtn
            return VNone(None)
                
        elif isinstance(line, Return):
            return [self.run_stmt(line.stmt, ctx)]
        elif isinstance(line, FuncDef):
            ctx[line.name] = Func(line.name, line, ctx)
        elif isinstance(line, FuncCall):
            target = Context(ctx) if line.target is None\
                else self.run_stmt(line.target, ctx)
            self.run_fn(line.fname, line.params, ctx, target)
        elif isinstance(line, ClassDef):
            props = {}
            constructor = None
            for subline in line.section.lines:
                if isinstance(subline, FuncDef):
                    if subline.name == line.name:
                        constructor = Func(subline.name, subline, ctx)
                        constructor.params.insert(0, [Var("this")])
                        constructor.params = [p for p in constructor.params if len(p) > 0]
                    else:
                        fn = Func(subline.name, subline, ctx)
                        fn.params.insert(0, [Var("this")])
                        fn.params = [p for p in fn.params if len(p) > 0]
                        props[subline.name] = fn
                elif isinstance(subline, Assignment):
                    val = self.run_stmt(subline.stmt, ctx)
                    props[subline.var] = val
            if line.subs:
                subs = [self.run_stmt(sub[0], ctx) for sub in line.subs]
            else:
                subs = []
            ctx[line.name] = Class(line.name, props, constructor, subs, ctx)
        elif isinstance(line, Import):
            try:
                modname = line.module_name.split("/")[-1]
                ctx[modname] = run_file(line.module_name+".pr")
            except ImportError:
                ctx[line.module_name] = PyModule(line.module_name)
        else:
            raise ProgramSyntaxError("No clue what this line is")

        self.last_line = (line, ran)

    def run(self, lines, ctx = None):
        if ctx is None:
            ctx = self.globals
        for line in lines:
            rtn = self.run_line(line, ctx)
            if isinstance(rtn, list): 
                #only Return can make rtn be a list
                #afaik
                return rtn[0]
        return VNone(None)

loaded_files = {}

def run_file(filepath:str):

    if filepath in loaded_files:
        return loaded_files[filepath]
    
    l = Lexer()
    p = Parser()
    i = Interpreter()
    try:
        with open(filepath) as file:
            text = file.read()
        
        tokens = l.tokenize(text)
        macrofied = l.apply_macros(tokens)
        i_tokens = p.parse(macrofied)
        if config.DEBUG_MODE:
            print(40*"-")
            print(",\nthen ".join(str(l) for l in i_tokens))
            print(40*"-")
        try:
            i.run(i_tokens)
        except KeyboardInterrupt:
            print("\nCtrl-C pressed, exiting...")
            sys.exit(0)

        
        module = Module(filepath.split(".")[0], i.globals)
        loaded_files[filepath] = module
        return module
        
    except FileNotFoundError as e:
        raise ImportError("File not found") from e