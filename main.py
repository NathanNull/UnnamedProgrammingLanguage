from __future__ import unicode_literals

# IT IS FINISHED(ish)

# TODO:
# more imports
# iter?

from interpreter import run_file
from sys import argv
import config

if len(argv) >= 2:
    if config:
        print(f"Running file {argv[1]}")
    run_file(argv[1])
else:
    run_file("test.pr")