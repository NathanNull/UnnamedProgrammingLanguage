import random

def shuffle(list):
    random.shuffle(list)
    return list

functions = [
    random.randint,
    random.choice,
    shuffle,
]