# ДЗ 1: print_list((1, (2, (3, ())))) → "(1 2 3)"

def print_list(pair):
    def create_result(pair):
        if pair == ():
            return ""
        head, tail = pair
        if tail == ():
            return str(head)
        return str(head) + " " + create_result(tail)
    print("(" + create_result(pair) + ")")

# Пример
print_list((1, (2, (3, ()))))  # -> (1 2 3)
