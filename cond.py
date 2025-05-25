from comparison_functions import less_than, greater_than, less_or_equal, greater_or_equal, equal
from evaluate import evaluate
from all_namespace import namespace

names = namespace()


def evaluate_condition(condition):
    try:
        if not isinstance(condition, tuple) or len(condition) != 2:
            raise ValueError("Некорректная структура условия")
        operator, pair = condition
        if not isinstance(operator, str):
            raise TypeError("Оператор должен быть строкой")
        if not isinstance(pair, tuple):
            raise TypeError("Операнды должны быть в кортеже")
        return True
    except Exception as e:
        if isinstance(e, (ValueError, TypeError)):
            raise
        raise ValueError(f"Ошибка при вычислении условия: {str(e)}")


def cond(*conditions):
    try:
        if not conditions:
            raise ValueError("Отсутствуют условия")
        for condition_pair in conditions:
            if not isinstance(condition_pair, tuple) or len(condition_pair) != 2:
                raise ValueError("Некорректная структура пары условие-значение")
            condition, value = condition_pair
            try:
                if evaluate_condition(condition) == 1:
                    return value
            except Exception as e:
                raise ValueError(f"Ошибка в условии {condition}: {str(e)}")
        return None
    except Exception as e:
        if isinstance(e, (ValueError, TypeError)):
            raise
        raise ValueError(f"Ошибка в операции cond: {str(e)}")


def if_function(args):
    """Макрос if: (if condition then_expr else_expr)"""
    if not args or not isinstance(args, tuple) or len(args) < 2:
        raise ValueError("if requires at least 2 arguments")

    condition = args[0]
    then_expr = args[1]
    else_expr = args[2] if len(args) > 2 else ()

    # Нужно получить доступ к пространству имен из контекста
    # Это будет передано через замыкание
    # Это будет передано через замыкание
    import inspect
    frame = inspect.currentframe()
    try:
        while frame:
            if 'names' in frame.f_locals:
                names = frame.f_locals['names']
                break
            frame = frame.f_back
        else:
            raise ValueError("Cannot find names in context")
    finally:
        del frame

    condition_result = evaluate(condition, names)

    if condition_result and condition_result != ():
        return evaluate(then_expr, names)
    else:
        return evaluate(else_expr, names)


def progn_function(args):
    """Функция progn: выполняет последовательность выражений и возвращает результат последнего"""
    if not args:
        return ()

    # Получаем пространство имен из контекста
    import inspect
    frame = inspect.currentframe()
    try:
        while frame:
            if 'names' in frame.f_locals:
                names = frame.f_locals['names']
                break
            frame = frame.f_back
        else:
            raise ValueError("Cannot find names in context")
    finally:
        del frame

    result = ()
    while args:
        if isinstance(args, tuple) and len(args) >= 2:
            result = evaluate(args[0], names)
            args = args[1]
        elif isinstance(args, tuple) and len(args) == 1:
            result = evaluate(args[0], names)
            break
        else:
            result = evaluate(args, names)
            break

    return result