def string_macro(args):
    if not args or not isinstance(args, tuple):
        raise ValueError("Неверный формат аргументов для string")

    value, _ = args
    if not isinstance(value, str):
        raise ValueError("Аргумент string должен быть строкой")

    return {"type": "string", "value": value.strip('"')}
