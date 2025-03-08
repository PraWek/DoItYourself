# ДЗ 2: функция умножения, (*)

def multiply(pair):
    if pair == ():
        return 1
    else:
        head, tail = pair
        return head * multiply(tail)

# Пример
print(multiply((4, (5, (6, ())))))  # -> 120
