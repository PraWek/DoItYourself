def array_macro(args):
    result = []
    current = args

    while current:
        if not isinstance(current, tuple):
            raise ValueError("Неверный формат аргументов для array")

        elem, current = current
        result.append(elem)

    return {"type": "array", "value": result}
