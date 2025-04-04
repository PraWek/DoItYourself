def dict_macro(args):
    result = {}
    while args:
        if not isinstance(args, tuple):
            raise ValueError("Неверный формат аргументов для dict")

        pair, args = args
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise ValueError("Каждый аргумент должен быть парой (ключ значение)")

        key, value = pair
        result[key] = value

    return {"type": "dict", "value": result}
