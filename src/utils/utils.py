def round(num, places):
    working = str(num - int(num))
    for i, e in enumerate(working[2:]):
        if e != '0':
            return int(num) + float(working[:i + 2 + places])
