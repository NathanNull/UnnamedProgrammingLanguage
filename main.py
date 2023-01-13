from __future__ import unicode_literals
# Programming language thing. Whee.
# Author: Nathan Strong
# Date: Novemberish 2022 - January 13, 2023
# Description: Indecipherable code to let you write
# more indecipherable code in *fancy new style!*
# Ok but seriously, this took a lot of effort and I
# think it came out well. No bugs (that I could find),
# a relatively intuitive syntax, and semi-acceptable
# speeds considering it's made in python.

# Don't mind the __prcache__.

from interpreter import run_file
from sys import argv
import config

if len(argv) >= 2:
    if config.DEBUG_MODE:
        print(f"Running file {argv[1]}")
    run_file(argv[1])
else:
    run_file("test.pr")