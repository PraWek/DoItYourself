def add(args):
    if not args:
        return 0
    total = 0
    while args:
        if isinstance(args, tuple) and len(args) >= 2:
            total += args[0]
            args = args[1]
        elif isinstance(args, tuple) and len(args) == 1:
            total += args[0]
            break
        else:
            total += args
            break
    return total


def subtract(args):
    if not args or (isinstance(args, tuple) and len(args) < 2):
        raise ValueError("subtract требует минимум 2 аргумента")

    if isinstance(args, tuple):
        result = args[0]
        args = args[1]
        while args:
            if isinstance(args, tuple) and len(args) >= 2:
                result -= args[0]
                args = args[1]
            elif isinstance(args, tuple) and len(args) == 1:
                result -= args[0]
                break
            else:
                result -= args
                break
    return result


def multiply(args):
    if not args:
        return 1
    result = 1
    while args:
        if isinstance(args, tuple) and len(args) >= 2:
            result *= args[0]
            args = args[1]
        elif isinstance(args, tuple) and len(args) == 1:
            result *= args[0]
            break
        else:
            result *= args
            break
    return result


def divide(args):
    if not args or (isinstance(args, tuple) and len(args) < 2):
        raise ValueError("divide требует минимум 2 аргумента")

    try:
        if isinstance(args, tuple):
            head = args[0]
            args = args[1]
            while args:
                if isinstance(args, tuple) and len(args) >= 2:
                    divisor = args[0]
                    if divisor == 0:
                        raise ValueError("Деление на ноль")
                    head = head / divisor
                    args = args[1]
                elif isinstance(args, tuple) and len(args) == 1:
                    divisor = args[0]
                    if divisor == 0:
                        raise ValueError("Деление на ноль")
                    head = head / divisor
                    break
                else:
                    if args == 0:
                        raise ValueError("Деление на ноль")
                    head = head / args
                    break
        return head
    except Exception as e:
        raise ValueError(f"Ошибка в операции деления: {str(e)}")