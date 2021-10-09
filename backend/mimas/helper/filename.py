def smart_io(filename, mode):
    if filename.endswith(".gz"):
        import gzip
        f = gzip.open(filename, mode)
    else:
        f = open(filename, mode)
    return f
