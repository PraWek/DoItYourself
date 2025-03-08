from check_pair import check_pair

def less_than(pair):
    check_pair(pair)
    head, tail = pair
    arg2 = tail[0]
    if head < arg2:
        return 1
    return ()

def greater_than(pair):
    check_pair(pair)
    head, tail = pair
    arg2 = tail[0]
    if head > arg2:
        return 1
    return ()

def less_or_equal(pair):
    check_pair(pair)
    head, tail = pair
    arg2 = tail[0]
    if head <= arg2:
        return 1
    return ()

def greater_or_equal(pair):
    check_pair(pair)
    head, tail = pair
    arg2 = tail[0]
    if head >= arg2:
        return 1
    return ()

def equal(pair):
    check_pair(pair)
    head, tail = pair
    arg2 = tail[0]
    if head == arg2:
        return 1
    return ()
