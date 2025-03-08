from check_pair import check_pair

def add(pair):
    if pair == ():
        return 0
    else:
        head, tail = pair
        return head + add(tail)

def subtract(pair):
    check_pair(pair)
    head, tail = pair
    return head - tail[0]

def multiply(pair):
    if pair == ():
        return 1
    else:
        head, tail = pair
        return head * multiply(tail)

def divide(pair):
    check_pair(pair)
    head, tail = pair
    return head / tail[0]
