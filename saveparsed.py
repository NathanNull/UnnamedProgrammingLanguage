import pickle, hmac, os
import config

key = 'sure is a key'.encode()

def save_parsed(filedata, parsed, filename):
    filekey = hmac.new(key, filedata.encode(), 'sha1').digest()
    data = pickle.dumps(parsed)

    dir = os.path.dirname(f'__prcache__/{filename}.{config.fileext}c')
    os.makedirs(dir, exist_ok=True)
    with open(f'__prcache__/{filename}.{config.fileext}c', 'wb') as file:
        file.write(filekey)
        file.write(data)

def test_parsed(filedata, filename):
    if not os.path.exists(f'__prcache__/{filename}.{config.fileext}c'):
        return None
    
    with open(f'__prcache__/{filename}.{config.fileext}c', 'rb') as file:
        filekey = file.read(20) # length of hmac key
        data = file.read()
        
    if filekey != hmac.new(key, filedata.encode(), 'sha1').digest():
        return None
    return pickle.loads(data)