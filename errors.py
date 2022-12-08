class ProgramSyntaxError(Exception):
    pass
class InvalidBracketing(ProgramSyntaxError):
    pass
class InvalidOperator(ProgramSyntaxError):
    pass
class Expected(ProgramSyntaxError):
    pass

class ProgramRuntimeError(Exception):
    pass
class ConversionError(ProgramRuntimeError):
    pass
class InvalidOperandType(ProgramRuntimeError):
    pass
class NotImplementedException(ProgramRuntimeError):
    pass
class InvalidValueType(ProgramRuntimeError):
    pass
class ImportError(ProgramRuntimeError):
    pass