import os



name = b'bnn2.exe'
paths = [b'movie2',b'arjun2.mkv']
file_path = name
# os.makedirs(name, exist_ok=True)
parent_dir = os.path.dirname(file_path)
if parent_dir != b'':
    os.makedirs(parent_dir,exist_ok=True) 


