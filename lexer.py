from ptoken import Word, Operator, Bracket,\
    MultilineBracket, Newline, StringLiteral,\
    ArgSep, HashDef, DoubleColon
from errors import InvalidOperator, ProgramSyntaxError
from random import randint

class Lexer:
    ops = "+-*/=<>&|.!"

    # Weird list comprehensiony thingy to create, for instance, + and += as legal ops.
    legal_ops = [itm for t in [
        "+","-","*","/",
        "<",">","<=",">=",
        "==","!=","&&","||",
        ".",
        "" # so = will be added
    ] for itm in (t, t+"=")]

    # Plus some unary-only ops
    legal_ops.extend(["!"])
    
    brackets = "()"
    ml_brackets = "{}"
    arr_brackets = "[]"
    lines = ";"
    argsep = ","
    quotes = "'\"" # looks a little weird but it's " and '
    
    def to_oneline(self, text):
        lines = [l.split("//")[0] for l in text.split("\n")]
        return "\n".join(lines).replace("\t", " ")
    
    def tokenize(self, text:str):
        oneline = self.to_oneline(text)
        tokens = [[]]
        self.mem = ""
        self.state = "gap"

        def ch_state(new, c):
            if self.state == "quote":
                if (new=="quote" and tokens[-1][-1].quote==c):
                    tokens[-1][-1].string = tokens[-1][-1].string.replace('\\n', '\n')
                    self.state = "gap"
                else:
                    tokens[-1][-1].string = tokens[-1][-1].string+c
                return
            elif self.state == "op":
                if new != "op" and tokens[-1][-1].op not in self.legal_ops:
                    raise InvalidOperator(f"Unidentified operator {tokens[-1][-1].op}")
            
            if new == "op":
                if self.state == "op":
                    tokens[-1][-1].op = tokens[-1][-1].op+c
                else:
                    tokens[-1].append(Operator(c))
            elif new == "bracket":
                tokens[-1].append(Bracket(c))
            elif new == "ml_bracket":
                tokens[-1].append(MultilineBracket(c))
            elif new == "arr_bracket":
                tokens[-1].append(Bracket(c))
            elif new == "line":
                tokens[-1].append(Newline())
            elif new == "argsep":
                tokens[-1].append(ArgSep())
            elif new == "colon":
                if self.state == "colon":
                    #make sure we don't count 1 colon
                    tokens[-1].append(DoubleColon())
            elif new == "quote":
                tokens[-1].append(StringLiteral(c, ""))
            elif new == "word":
                if self.state != "word":
                    tokens[-1].append(Word(c))
                else:
                    tokens[-1][-1].word = tokens[-1][-1].word+c
            elif new == 'hashdef':
                tokens[-1].append(HashDef())
            self.state = new
        
        for c in oneline:
            if c in self.ops:
                ch_state("op", c)
            elif c in self.brackets:
                ch_state("bracket", c)
            elif c in self.ml_brackets:
                ch_state("ml_bracket", c)
            elif c in self.arr_brackets:
                ch_state("arr_bracket", c)
            elif c in self.lines:
                ch_state("line", c)
            elif c in self.argsep:
                ch_state("argsep", c)
            elif c in self.quotes:
                ch_state("quote", c)
            elif c == " ":
                ch_state("gap", c)
            elif c == "#":
                ch_state("hashdef", c)
            elif c == ":":
                ch_state("colon", c)
            elif c == "\n":
                tokens.append([])
                ch_state("gap", c)
            else:
                ch_state("word", c)
                self.mem = self.mem + c

        ch_state("gap", c)
        return tokens

    def replace(self, tokens, defs):
        newline = []
        replaced = False
        for tk in tokens:
            if isinstance(tk, Word) and tk.word in defs:
                newline.extend(defs[tk.word])
                replaced = True
            else:
                newline.append(tk)
        if replaced:
            return self.replace(newline, defs)
        return newline

    def apply_macros(self, tokens, rtn_macros=False):
        defs = {}
        new_tokens = []
        state = 'normal'
        mem = ["",[]]
        for line in tokens:
            if state == 'mldef':
                if len(line) == 1 and isinstance(line[0], HashDef):
                    state = 'normal'
                    defs[mem[0]] = mem[1]
                else:
                    mem[1].extend(line)
                continue
            elif state == 'ifdef':
                if len(line) == 1 and isinstance(line[0], HashDef):
                    state = 'normal'
                    continue
                if not mem:
                    continue
            elif not line:
                # ignore empty lines
                continue
            # check for # at start of line
            if isinstance(line[0], HashDef):
                if not (isinstance(line[1], Word)\
                        and line[1].word in [
                            'define', 'importdefs', 
                            'define_multi', 'funcdef',
                            'ifdef', 'ifundef', 'undef',
                            'funcdef_multi'
                        ]):
                    raise ProgramSyntaxError("Malformed # statement")
                if line[1].word == 'define':
                    defs[line[2].word] = line[3:]
                elif line[1].word == 'importdefs':
                    filename = ''.join(str(t) for t in line[2:])
                    with open(filename+'.prm') as macrofile:
                        lines = self.tokenize(macrofile.read())
                    extra, macros = self.apply_macros(lines, True)
                    for name, rep in macros.items():
                        defs[name] = rep
                    if extra:
                        new_tokens.append(extra)
                elif line[1].word == 'define_multi':
                    state = 'mldef'
                    mem = [line[2].word, []]
                elif 'funcdef' in line[1].word:
                    if not sum(1 for t in line if isinstance(t,DoubleColon)) == 1:
                        raise ProgramSyntaxError(
                            'Malformed #funcdef (expected exactly one ::)')
                    # get index of double colon
                    dc_i = next(
                        i for i,v in enumerate(line) if isinstance(v, DoubleColon)
                    )
    
                    if not isinstance(line[3], Bracket):
                        raise ProgramSyntaxError(
                            'Malformed #funcdef (expected \'(\')')
                    
                    params = []
                    skip = False
                    for t in line[4:dc_i-1]:
                        if not skip:
                            params.append(t)
                        else:
                            if not isinstance(t, ArgSep):
                                raise ProgramSyntaxError(
                                    'Malformed #funcdef (expected ,)'
                                )
                        skip = not skip

                    fname = f'macrofn_{randint(10000, 99999)}_{line[2].word}'
                    if 'multi' in line[1].word:
                        fn = self.tokenize(
                f"func {fname}({','.join(t.word for t in params)})"'{'
                        )[0]+\
                        self.replace([line[dc_i+1]], defs)+\
                        self.tokenize(
                            '}'
                        )[0]
                    else:
                        fn = self.tokenize(
                f"func {fname}({','.join(t.word for t in params)})"'{return'
                        )[0]+\
                        self.replace(line[dc_i+1:], defs)+\
                        self.tokenize(
                            ';}'
                        )[0]
                    new_tokens.append(fn)
                    defs[line[2].word] = [Word(fname)]
                elif line[1].word == 'ifdef':
                    state = 'ifdef'
                    mem = line[2].word in defs
                elif line[1].word == 'ifundef':
                    state = 'ifdef'
                    mem = line[2].word not in defs
                elif line[1].word == 'undef':
                    del defs[line[2].word]
            else:
                new_tokens.append(self.replace(line, defs))

        # flatten + return
        if rtn_macros:
            return [i for sl in new_tokens for i in sl], defs
        return [i for sl in new_tokens for i in sl]