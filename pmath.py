import math

def sign(x):
    return math.copysign(1, x)
def lcm(a, b):
    return (a*b)/math.gcd(a,b)

functions = [
    math.ceil,
    math.factorial,
    math.floor,
    math.gcd,
    lcm,
    
    math.pow,
    math.log,
    math.sqrt,
    
    math.cos,
    math.sin,
    math.tan,
    math.acos,
    math.asin,
    math.atan,
    math.atan2,

    math.dist,
    math.radians,
    math.degrees,
]

variables = {
    'pi': math.pi,
    'e': math.e,
    'tau': math.tau,
    'inf': math.inf
}