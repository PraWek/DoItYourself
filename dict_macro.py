def dict_macro(args):
    if not args:
        return {"type": "dict", "value": {}}

    result = {}
    current = args
    while current:
        if not isinstance(current, tuple) or len(current) != 2:
            raise ValueError("Неверный формат аргументов для dict")

        pair, current = current
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise ValueError("Каждый аргумент должен быть парой (ключ значение)")

        key, value_tuple = pair
        if not isinstance(value_tuple, tuple) or len(value_tuple) != 2:
            raise ValueError("Неверный формат значения")

        value, _ = value_tuple
        result[key] = value

    return {"type": "dict", "value": result}
