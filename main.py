from __future__ import unicode_literals
# IT IS FINISHED (well, kinda)
# It's currently technically usable

# Right, so the python import thing is wayy more
# complicated than I was expecting. It'd probably
# be easier in something like C# that actually
# has proper typing built in. Too far in to stop
# now, though. Instead I think I'll just develop
# the core language further.

from interpreter import run_file
from sys import argv
import config

if len(argv) >= 2:
    if config:
        print(f"Running file {argv[1]}")
    run_file(argv[1])
else:
    run_file("example.pr")