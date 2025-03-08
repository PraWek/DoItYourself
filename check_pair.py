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
    if len(pair) != 2:
        return "Функция принимает ровно два аргумента"
