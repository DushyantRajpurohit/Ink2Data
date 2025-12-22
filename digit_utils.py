MAP = {
    "०":"0","१":"1","२":"2","३":"3","४":"4",
    "५":"5","६":"6","७":"7","८":"8","९":"9"
}

def normalize_digits(text):
    if not text:
        return text
    for k,v in MAP.items():
        text = text.replace(k,v)
    return text