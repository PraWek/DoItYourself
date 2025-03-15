from check_pair import check_pair

def validate_numeric_operands(head, tail):
    if not isinstance(head, (int, float)) or not isinstance(tail[0], (int, float)):
        raise TypeError("Операнды должны быть числами")
    if not tail or len(tail) < 1:
        raise ValueError("Отсутствует второй операнд")

def less_than(pair):
    try:
        check_pair(pair)
        head, tail = pair
        validate_numeric_operands(head, tail)
        arg2 = tail[0]
        if head < arg2:
            return 1
        return ()
    except Exception as e:
        raise ValueError(f"Ошибка в операции '<': {str(e)}")

def greater_than(pair):
    try:
        check_pair(pair)
        head, tail = pair
        validate_numeric_operands(head, tail)
        arg2 = tail[0]
        if head > arg2:
            return 1
        return ()
    except Exception as e:
        raise ValueError(f"Ошибка в операции '>': {str(e)}")

def less_or_equal(pair):
    try:
        check_pair(pair)
        head, tail = pair
        validate_numeric_operands(head, tail)
        arg2 = tail[0]
        if head <= arg2:
            return 1
        return ()
    except Exception as e:
        raise ValueError(f"Ошибка в операции '<=': {str(e)}")

def greater_or_equal(pair):
    try:
        check_pair(pair)
        head, tail = pair
        validate_numeric_operands(head, tail)
        arg2 = tail[0]
        if head >= arg2:
            return 1
        return ()
    except Exception as e:
        raise ValueError(f"Ошибка в операции '>=': {str(e)}")

def equal(pair):
    try:
        check_pair(pair)
        head, tail = pair
        validate_numeric_operands(head, tail)
        arg2 = tail[0]
        if head == arg2:
            return 1
        return ()
    except Exception as e:
        raise ValueError(f"Ошибка в операции '==': {str(e)}")
