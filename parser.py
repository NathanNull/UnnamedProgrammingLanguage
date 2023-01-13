from ptoken import Bracket, MultilineBracket, Word,\
    Newline, Operator, StringLiteral, ArgSep
from i_token import MultilineSection, Section,\
    BinaryOperator, Assignment, CompoundAssignment,\
    Var, Keyword, keywords, AcceptsSection,\
    IfStatement, WhileLoop, FuncDef, FuncCall, Tuple,\
    Return, ArrayLiteral, GetProperty,\
    ElseStatement, Import, ClassDef,\
    ArrIdx, ForLoop, UnaryOperator
from ptypes import String, Int, Float, Bool
from errors import InvalidBracketing, Expected,\
    ProgramSyntaxError
import config

class Parser:
    def pair_brackets(self, tokens, b_type, _make_tuple=False):
        bracketed = []
        state = "searching"
        for token in tokens:
            if state == "searching":
                if isinstance(token, Bracket) and token.opening:
                    to_bracket = []
                    btype = token.type
                    b_depth = 1
                    all_bdepth = 1
                    state = "find_end"
                    found_argsep = False
                else:
                    bracketed.append(token)
            elif state == "find_end":
                if isinstance(token, Bracket):
                    val = 1 if token.opening else -1
                    if token.type == btype:
                        b_depth += val
                    all_bdepth += val
                elif isinstance(token, ArgSep) and all_bdepth == 1:
                    found_argsep = True
                if b_depth > 0:
                    to_bracket.append(token)
                else:
                    bracketed.append(self.pair_brackets(to_bracket, btype, found_argsep))
                    state = "searching"

        if state == "find_end":
            print([str(t) for t in tokens])
            print([str(t) for t in bracketed])
            raise InvalidBracketing("Unexpected newline")

        if _make_tuple or b_type == 1:
            vals = [[]]
            for tk in bracketed:
                if isinstance(tk, ArgSep):
                    vals.append([])
                else:
                    vals[-1].append(tk)
            if b_type == 1:
                return ArrayLiteral(vals)
            else:
                return Tuple(vals)
        
        return Section(bracketed)

    def parse_words(self, tokens, depth=0):
        # Convert Word to String, Int, Float
        lit_tokens = []
        for token in tokens:
            if isinstance(token, Word):
                is_num = True
                for c in token.word:
                    if c not in "1234567890":
                        is_num = False
                
                if is_num:
                    new_token = Int(int(token.word))
                    if len(lit_tokens) >= 2:
                        last = lit_tokens[-1]
                        sec_last = lit_tokens[-2]
                        # Seems like kind of a weird fix but it works ig.
                        # If tokens look like this: [8475, ".", 754]
                        # You get this: [8475.754]
                        if isinstance(last, Operator) and last.op == "."\
                        and isinstance(sec_last, Int):
                            lit_tokens.pop()
                            lit_tokens.pop()
                            new_token = Float(float(f"{sec_last.val}.{token.word}"))
                elif token.word in keywords:
                    new_token = keywords[token.word]
                elif token.word in ["true", "false"]:
                    new_token = Bool(token.word == "true")
                else:
                    new_token = Var(token.word)
            elif isinstance(token, StringLiteral):
                new_token = String(token.string)
            elif isinstance(token, Section):
                token.inner_tokens = self.parse_words(token.inner_tokens, depth+1)
                new_token = token
            elif isinstance(token, Operator) and lit_tokens and isinstance(lit_tokens[-1], Keyword) and lit_tokens[-1].kw == "func":
                new_token = Var(f'__op_{token.op}__')
            else:
                new_token = token

            lit_tokens.append(new_token)
        return lit_tokens

    def parse_ops(self, tokens):
        op_tokens = tokens
        # Order should mimic this:
        # https://learn.microsoft.com/en-us/cpp/c-language/precedence-and-order-of-evaluation?view=msvc-170
        ops = [
            ["!"],
            ["*", "/"],
            ["+", "-"],
            ["<<", ">>"],
            [">","<","<=",">="],
            ["==", "!="],
            ["&"], ["^"], ["|"],
            ["&&"], ["||"]
        ]
        for op in ops:
            op_tokens = self.parse_op_grp(op_tokens, op)
        return op_tokens
        
    def parse_op_grp(self, tokens, op, depth=0):
        # Have operators grab what's to the left and right of them
        op_tokens = []
        state = "normal"
        state_stack = []
        for token in tokens:
            new_state = "normal"
            if isinstance(token, Operator) and token.op in op:
                try:
                    # Weird assertion stuff to test for potential unary ops
                    assert (not isinstance(op_tokens[-1], BinaryOperator)\
                            or op_tokens[-1].rhs is not None)
                    if state_stack:
                        assert not isinstance(op_tokens[-1], UnaryOperator)
                    lhs = op_tokens.pop()
                    new_token = BinaryOperator(lhs, token.op, None)
                    new_state = "get_rhs"
                except (IndexError, AssertionError): #pop from empty list
                    state_stack.append(state)
                    state = "normal"
                    new_state = "get_unary"
                    new_token = UnaryOperator(token.op, None)
            elif isinstance(token, Section):
                token.inner_tokens = self.parse_op_grp(token.inner_tokens, op, depth+1)
                new_token = token
            elif isinstance(token, Tuple):
                token.vals = [self.parse_op_grp(v, op, depth+1) for v in token.vals]
                new_token = token
            elif isinstance(token, ArrayLiteral):
                token.vals = [i for i in token.vals if not (isinstance(i, list) and len(i)==0)]
                token.vals = [
                    self.parse_op_grp(v, op, depth+1)[0] if isinstance(v,list) else v\
                    for v in token.vals
                ]
                new_token = token
            elif isinstance(token, ArrIdx):
                token.var = self.parse_op_grp([token.var], op, depth+1)[0]
                token.idx_stmt.vals = [
                    self.parse_op_grp([v], op, depth+1)[0] for v in token.idx_stmt.vals
                ]
                new_token = token
            elif isinstance(token, FuncCall):
                token.params.vals = [
                    self.parse_op_grp(p, op, depth+1) for p in token.params.vals
                ]
                new_token = token
            elif isinstance(token, BinaryOperator):
                for op_tkn in (token.lhs, token.rhs):
                    if isinstance(op_tkn, Section):
                        op_tkn.inner_tokens = self.parse_op_grp(
                            op_tkn.inner_tokens, op, depth+1
                        )
                new_token = token
            else:
                new_token = token

            while True:# It's weird but I think it works.
                if state == "normal":
                    op_tokens.append(new_token)
                elif state == "get_rhs":
                    try:
                        op_tokens[-1].rhs = new_token
                    except:
                        print(op_tokens, state_stack, new_token)
                        raise
                elif state == "get_unary":
                    op_tokens[-1].rhs = new_token
                    state = state_stack.pop()
                    new_token = op_tokens.pop()
                    continue
                break
            state = new_state
        return op_tokens

    def equal_brackets(self, tokens):
        num_l = 0
        num_r = 0
        for t in tokens:
            if isinstance(t, Bracket) and t.type == 0:
                if t.opening:
                    num_l += 1
                else:
                    num_r += 1
        return num_l == num_r
    
    def find_lines(self, tokens):
        lines = [[]]
        for token in tokens:
            if isinstance(token, Newline):
                lines.append([])
            elif isinstance(token, MultilineBracket):
                if not token.opening:
                    lines.pop()
                lines.append(token)
                lines.append([])
            else:
                curr = lines[-1]
                if len(curr) >= 2\
                and isinstance(curr[0], Keyword)\
                and curr[0].kw in ["if", "while"]\
                and isinstance(curr[1], Bracket)\
                and curr[1].opening\
                and isinstance(curr[-1], Bracket)\
                and not curr[-1].opening\
                and self.equal_brackets(curr):
                    lines.append([])
                elif len(curr) == 1\
                and isinstance(curr[0], Keyword)\
                and curr[0].kw == "else":
                    lines.append([])
                lines[-1].append(token)
        
        if lines.pop():
            raise Expected("Expected newline, got EOF")
        gml = self.group_multiline(lines)
        return gml

    def group_multiline(self, lines):
        pstr = lambda t: str([str(t2) for t2 in t]) if isinstance(t, list) else str(t)
        new_lines = []
        state = "search"
        for line in lines:
            if state == "search":
                if isinstance(line, MultilineBracket):
                    state = "find_end"
                    to_bracket = []
                    depth = 1
                else:
                    new_lines.append(line)
            elif state == "find_end":
                if isinstance(line, MultilineBracket):
                    if line.opening:
                        depth += 1
                    else: 
                        depth -= 1
                        
                    if depth == 0:
                        new_lines.append(
                            MultilineSection(self.group_multiline(to_bracket))
                        )
                        state = "search"
                    else:
                        to_bracket.append(line)
                else:
                    to_bracket.append(line)
        if state == "find_end":
            print("\n".join(pstr(t) for t in to_bracket))
            raise Exception("Unclosed {")

        return new_lines
    
    def detect_stmt_type(self, line, last):
        if len(line) == 3\
        and (isinstance(line[0], Var)\
            or isinstance(line[0], GetProperty)\
            or isinstance(line[0], ArrIdx))\
        and isinstance(line[1], Operator)\
        and line[1].op[-1] == "=":
            if isinstance(line[0], Var):
                target = None
                var = line[0].name
                idx = None
            elif isinstance(line[0], GetProperty):
                target = line[0].target
                var = line[0].prop
                idx = None
            else:
                target = line[0].var
                var = None
                idx = line[0].idx_stmt
            if len(line[1].op) > 1:
                # Oh boy I do love &&=
                return CompoundAssignment(target, var, line[1].op[:-1], line[2], idx)
            return Assignment(target, var, line[2], idx)
        elif len(line) == 2\
        and isinstance(line[0], Keyword)\
        and isinstance(line[1], Section):
            if line[0].kw == "if":
                return IfStatement(line[1].inner_tokens)
            elif line[0].kw == "while":
                return WhileLoop(line[1].inner_tokens)
        elif len(line) == 4\
        and isinstance(line[0], Keyword)\
        and line[0].kw == "for"\
        and isinstance(line[1], Var)\
        and isinstance(line[2], Keyword)\
        and line[2].kw == "in"\
        and isinstance(line[3], Section):
            return ForLoop(line[1].name, line[3])
        elif len(line) == 1\
        and isinstance(line[0], Keyword)\
        and line[0].kw == "else":
            return ElseStatement()
        elif len(line) == 2\
        and isinstance(line[0], Keyword)\
        and line[0].kw in ["func", "class"]\
        and isinstance(line[1], FuncCall):
            if line[0].kw == "func":
                return FuncDef(line[1].fname, line[1].params.vals)
            elif line[0].kw == "class":
                return ClassDef(line[1].fname, line[1].params.vals)
        elif len(line) == 1 and isinstance(line[0], FuncCall):
            return line[0]
        elif len(line) == 2\
        and isinstance(line[0], Keyword):
            if line[0].kw == "return":
                return Return(line[1])
            elif line[0].kw == "import":
                if isinstance(line[1], String):
                    return Import(line[1].val)
                else:
                    raise ProgramSyntaxError("need string for import")
        else:
            print([(str(t), type(t)) for t in line])
            raise ProgramSyntaxError("No clue what this line is")

    def parse_fns(self, tokens, depth=0):
        new_tokens = []
        for tk in tokens:
            if isinstance(tk, Section):
                tki = self.parse_fns(tk.inner_tokens, depth+1)
                tk.inner_tokens = self.parse_ops(tki)
            elif isinstance(tk, ArrIdx):
                def arr_fns(t):
                    newvals = []
                    for stmt in t.idx_stmt.vals:
                        nv = self.parse_fns([stmt], depth+1)
                        nv = self.parse_ops(nv)[0]
                        newvals.append(nv)
                    t.idx_stmt.vals = newvals
                    if isinstance(t.var, ArrIdx):
                        arr_fns(t.var)
                arr_fns(tk)
            if (
                isinstance(tk, Tuple) 
                or (isinstance(tk, Section) and len(tk.inner_tokens)<=1)
            )\
            and len(new_tokens)>0\
            and any(isinstance(new_tokens[-1], t) for t in (Var, GetProperty)):
                # make a function
                params = tk
                if isinstance(tk, Section):
                    params = Tuple([tk.inner_tokens])
                params.vals = [self.parse_fns(p) for p in params.vals]
                func = new_tokens.pop()
                if isinstance(func, GetProperty):
                    target = func.target
                    name = func.prop
                else:
                    target = None
                    name = func.name
                new_tokens.append(FuncCall(target, name, params))
            elif isinstance(tk, ArrayLiteral)\
            and len(new_tokens)>0\
            and not isinstance(new_tokens[-1], Operator):
                # make an arridx (arr could be a GetProperty but it doesn't matter)
                arr = new_tokens.pop()
                aix = ArrIdx(arr, ArrayLiteral([t[0] for t in tk.vals]))
                new_tokens.append(aix)
            else:
                new_tokens.append(tk)
            try:
                dot = new_tokens[-2]
                if isinstance(dot, Operator) and dot.op == ".":
                    target = new_tokens[-3]
                    get = new_tokens[-1]
                    for _ in range(3):
                        new_tokens.pop()
                    new_tokens.append(GetProperty(target, get.name))
            except:
                pass
        return new_tokens

    def parse_line(self, line, prev):
        if isinstance(line, MultilineSection):
            if not isinstance(prev, AcceptsSection):
                print(prev)
                raise InvalidBracketing("Multiline bracket for no reason")
            new = []
            p = None
            for subline in line.lines:
                parsed, assign_prev = self.parse_line(subline, p)
                if parsed is not None:
                    new.append(parsed)
                p = parsed if assign_prev is None else assign_prev
            line.lines = new
            prev.section = line
            return None, None
        bracketed = self.pair_brackets(line, 0).inner_tokens
        #arr_idx = self.parse_arridx(bracketed)
        func_call = self.parse_fns(bracketed)
        op_tokens = self.parse_ops(func_call)
        stmt_line = self.detect_stmt_type(op_tokens, prev)
        if isinstance(prev, AcceptsSection):
            prev.section = MultilineSection([stmt_line])
            return None, stmt_line
        else:
            return stmt_line, None
    
    def parse(self, tokens):
        lit_tokens = self.parse_words(tokens)
        lines = self.find_lines(lit_tokens)
        line_tokens = []
        prev = None
        for line in lines:
            if config.DEBUG_MODE:
                print([str(l) for l in line] if isinstance(line, list) else line)
            parsed, assign_prev = self.parse_line(line, prev)
            if parsed is not None:
                line_tokens.append(parsed)
            prev = parsed if assign_prev is None else assign_prev
        return line_tokens