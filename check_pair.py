def print_list(pair):
    def create_result(pair):
        if pair == ():
            return ""
        head, tail = pair
        if tail == ():
            return str(head)
        return str(head) + " " + create_result(tail)
    print("(" + create_result(pair) + ")")

def check_pair(pair):
    if not isinstance(pair, tuple):
        raise TypeError("Аргумент должен быть кортежем")
    if len(pair) != 2:
        raise ValueError("Пара должна содержать ровно два элемента")
    if not isinstance(pair[1], tuple):
        raise TypeError("Второй элемент пары должен быть кортежем")
