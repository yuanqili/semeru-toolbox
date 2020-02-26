def load_src(path, template):
    with open(path) as f:
        src = f.read()
    for k, v in template.items():
        src = src.replace(k, v)
    return src
