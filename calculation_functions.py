from check_pair import check_pair


def add(pair):
    """
    (+ 1 2 3) = 6
    """
    if pair == ():
        return 0
    else:
        head, tail = pair
        if isinstance(tail, tuple):
            return head + add(tail)
        return head + tail


def subtract(pair):
    """
    (- 5 3) = 2
    """
    try:
        check_pair(pair)
        head, tail = pair
        if not tail:
            raise ValueError("Требуется как минимум 2 числа для вычитания")
        return head - add(tail)
    except Exception as e:
        raise ValueError(f"Ошибка в операции вычитания: {str(e)}")


def multiply(pair):
    """
    (* 2 3 4) = 24
    """
    if pair == ():
        return 1
    else:
        head, tail = pair
        return head * multiply(tail)


def divide(pair):
    """
    (/ 24 2 3) = 4
    """
    try:
        check_pair(pair)
        head, tail = pair
        if not tail:
            raise ValueError("Требуется как минимум 2 числа для деления")

        divisor = multiply(tail)
        if divisor == 0:
            raise ValueError("Деление на ноль")

        return head / divisor
    except Exception as e:
        raise ValueError(f"Ошибка в операции деления: {str(e)}")
