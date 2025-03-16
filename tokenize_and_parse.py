def tokenize(line):
    tokens = []
    current_token = ''
    in_quotes = False
    i = 0
    while i < len(line):
        char = line[i]
        if char == '"':
            if current_token and not in_quotes:
                tokens.append(current_token)
                current_token = ''
            in_quotes = not in_quotes
            current_token += char
        elif char == ' ' and not in_quotes:
            if current_token:
                tokens.append(current_token)
                current_token = ''
        elif char == '(' or char == ')' and not in_quotes:
            if current_token:
                tokens.append(current_token)
                current_token = ''
            tokens.append(char)
        else:
            current_token += char
        i += 1
    if current_token:
        tokens.append(current_token)
    return tokens


def parse(tokens):
    if not tokens:
        raise SyntaxError("Unexpected EOF")

    token = tokens.pop(0)

    if token == '(':
        lst = []
        while tokens and tokens[0] != ')':
            lst.append(parse(tokens))
        if not tokens:
            raise SyntaxError("Отсутствует закрывающая скобка")
        tokens.pop(0)
        return tuple(lst[0] if len(lst) == 1 else lst[0] if len(lst) == 0 else (lst[0], tuple(lst[1:])))
    elif token.startswith('"') and token.endswith('"'):
        return {"type": "string", "value": token[1:-1]}
    elif token.startswith('['):
        if not token == '[':
            raise SyntaxError("Недопустимый синтаксис массива")
        arr = []
        while tokens and tokens[0] != ']':
            arr.append(parse(tokens))
        if not tokens:
            raise SyntaxError("Отсутствует закрывающая скобка")
        tokens.pop(0)
        return {"type": "array", "value": arr}
    elif token.startswith('{'):
        if not token == '{':
            raise SyntaxError("Недопустимый синтаксис словаря")
        dict_items = {}
        while tokens and tokens[0] != '}':
            key = parse(tokens)
            if not tokens or tokens[0] != ':':
                raise SyntaxError("Пропущенное двоеточие в словаре")
            tokens.pop(0)
            if not tokens:
                raise SyntaxError("Пропущенное значение в словаре")
            value = parse(tokens)
            dict_items[key] = value
        if not tokens:
            raise SyntaxError("Отсутствует закрывающая фигурная скобка")
        tokens.pop(0)
        return {"type": "dict", "value": dict_items}
    elif token == ']' or token == '}' or token == ')':
        raise SyntaxError(f"Unexpected {token}")
    else:
        try:
            return int(token)
        except ValueError:
            try:
                return float(token)
            except ValueError:
                return token