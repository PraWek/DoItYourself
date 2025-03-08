def tokenize(line):
    tokens = []
    current_token = ''
    in_quotes = False
    for char in line:
        if char == ' ' and not in_quotes:
            if current_token:
                tokens.append(current_token)
                current_token = ''
        elif char == '(' or char == ')':
            if current_token:
                tokens.append(current_token)
                current_token = ''
            tokens.append(char)
        else:
            current_token += char
    if current_token:
        tokens.append(current_token)
    return tokens


def parse(tokens):
    if not tokens:
        raise SyntaxError("Unexpected EOF")

    token = tokens.pop(0)

    if token == '(':
        lst = []
        while tokens[0] != ')':
            lst.append(parse(tokens))
        tokens.pop(0)  # Убираем закрывающую скобку
        return lst
    elif token == ')':
        raise SyntaxError("Unexpected )")
    else:
        try:
            return int(token)
        except ValueError:
            try:
                return float(token)
            except ValueError:
                return token