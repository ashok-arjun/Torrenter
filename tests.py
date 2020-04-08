files = [{'index': 0},{'index': 1},{'index': 2}]

for f in files[:]:
    print(f)
    files.remove(f)
print(files)