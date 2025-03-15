from check_pair import check_pair

def add(pair):
    try:
        if pair == ():
            return 0
        head, tail = pair
        if not isinstance(head, (int, float)):
            raise TypeError("Аргументы должны быть числами")
        return head + add(tail)
    except Exception as e:
        raise ValueError(f"Ошибка в операции сложения: {str(e)}")

def subtract(pair):
    try:
        check_pair(pair)
        head, tail = pair
        if not isinstance(head, (int, float)) or not isinstance(tail[0], (int, float)):
            raise TypeError("Аргументы должны быть числами")
        return head - tail[0]
    except Exception as e:
        raise ValueError(f"Ошибка в операции вычитания: {str(e)}")

def multiply(pair):
    try:
        if pair == ():
            return 1
        head, tail = pair
        if not isinstance(head, (int, float)):
            raise TypeError("Аргументы должны быть числами")
        return head * multiply(tail)
    except Exception as e:
        raise ValueError(f"Ошибка в операции умножения: {str(e)}")

def divide(pair):
    try:
        check_pair(pair)
        head, tail = pair
        if not isinstance(head, (int, float)) or not isinstance(tail[0], (int, float)):
            raise TypeError("Аргументы должны быть числами")
        if tail[0] == 0:
            raise ZeroDivisionError("Деление на ноль")
        return head / tail[0]
    except Exception as e:
        raise ValueError(f"Ошибка в операции деления: {str(e)}")
