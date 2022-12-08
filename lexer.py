from ptoken import Word, Operator, Bracket,\
    MultilineBracket, Newline, StringLiteral,\
    ArgSep
from errors import InvalidOperator

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

    # Plus some unary ops
    legal_ops.extend(["!"])
    
    brackets = "()"
    ml_brackets = "{}"
    arr_brackets = "[]"
    lines = ";"
    argsep = ","
    quotes = "'\"" # looks a little weird but it's " and '
    
    def to_oneline(self, text):
        lines = [l.split("//")[0] for l in text.split("\n")]
        return " ".join(lines).replace("\t", " ")
    
    def tokenize(self, text:str):
        oneline = self.to_oneline(text)
        tokens = []
        self.mem = ""
        self.state = "gap"

        def ch_state(new, c):
            if self.state == "quote":
                if (new=="quote" and tokens[-1].quote==c):
                    self.state = "gap"
                else:
                    tokens[-1].string = tokens[-1].string+c
                return
            elif self.state == "op":
                if new != "op" and tokens[-1].op not in self.legal_ops:
                    raise InvalidOperator(f"Unidentified operator {tokens[-1].op}")
            
            if new == "op":
                if self.state == "op":
                    tokens[-1].op = tokens[-1].op+c
                else:
                    tokens.append(Operator(c))
            elif new == "bracket":
                tokens.append(Bracket(c))
            elif new == "ml_bracket":
                tokens.append(MultilineBracket(c))
            elif new == "arr_bracket":
                tokens.append(Bracket(c))
            elif new == "line":
                tokens.append(Newline())
            elif new == "argsep":
                tokens.append(ArgSep())
            elif new == "quote":
                tokens.append(StringLiteral(c, ""))
            elif new == "word":
                if self.state != "word":
                    tokens.append(Word(c))
                else:
                    tokens[-1].word = tokens[-1].word+c
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
            else:
                ch_state("word", c)
                self.mem = self.mem + c

        ch_state("gap", c)
        return tokens