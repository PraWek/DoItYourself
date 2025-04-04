from array_macro import array_macro
from dict_macro import dict_macro
from string_macro import string_macro


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
        elif char in '(){}:,' and not in_quotes:
            if current_token:
                tokens.append(current_token)
                current_token = ''
            if char != ',':
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
    elif token == '(':
        elements = []
        while tokens and tokens[0] != ')':
            elements.append(parse(tokens))
        if not tokens:
            raise SyntaxError("Отсутствует закрывающая скобка")
        tokens.pop(0)

        # Проверяем тип макроса
        if elements:
            if elements[0] == 'dict':
                return dict_macro(tuple(elements[1:]))
            elif elements[0] == 'string':
                return string_macro(tuple(elements[1:]))
            elif elements[0] == 'array':
                return array_macro(tuple(elements[1:]))
        return tuple(elements)
    elif token == '(':
        elements = []
        while tokens and tokens[0] != ')':
            elements.append(parse(tokens))
        if not tokens:
            raise SyntaxError("Отсутствует закрывающая скобка")
        tokens.pop(0)

        # Если это вызов dict
        if elements and elements[0] == 'dict':
            return dict_macro(tuple(elements[1:]))
        return tuple(elements)

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