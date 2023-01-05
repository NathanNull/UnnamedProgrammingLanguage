class Token:
    pass

class Word(Token):
    def __init__(self, word):
        self.word = word

    def __str__(self):
        return self.word

class Operator(Token):
    def __init__(self, op):
        self.op = op

    def __str__(self):
        return self.op

class Bracket(Token):
    def __init__(self, bracket):
        self.bracket = bracket
        if bracket in "()":
            self.type = 0
        elif bracket in "[]":
            self.type = 1
        self.opening = bracket in "(["

    def __str__(self):
        return self.bracket

class MultilineBracket(Token):
    def __init__(self, bracket):
        self.bracket = bracket
        self.type = 2
        self.opening = bracket == "{"
        self.attached = None

    def __str__(self):
        return self.bracket

class Newline(Token):
    def __str__(self):
        return "NEWLINE"

class StringLiteral(Token):
    def __init__(self, quote, string):
        self.quote = quote
        self.string = string

    def __str__(self):
        return self.quote+self.string+self.quote

class HashDef(Token):
    def __str__(self):
        return '#'

class DoubleColon(Token):
    def __str__(self):
        return '::'

class ArgSep(Token):
    def __str__(self):
        return "ARGSEP"