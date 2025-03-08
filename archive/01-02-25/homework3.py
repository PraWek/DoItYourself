# ДЗ 3: функция деления, (/)

def check_pair(pair):
    if len(pair) != 2:
        return "Функция принимает ровно два аргумента"

def divide(pair):
    check_pair(pair)
    head, tail = pair
    return head / tail[0]

# Пример
print(divide((6, (2, ()))))  # -> 3.0
