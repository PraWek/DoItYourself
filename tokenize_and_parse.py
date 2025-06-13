import re


def tokenize(code):
    """Разбивает код на токены"""
    # Регулярное выражение для токенов
    token_pattern = r'''
        \s*                    # пропустить пробелы
        (?:
            ;.*$               # комментарии
            |
            \(                 # открывающая скобка
            |
            \)                 # закрывающая скобка
            |
            "(?:[^"\\]|\\.)*"  # строка в кавычках
            |
            [^\s()"';]+        # другие токены
        )
    '''

    tokens = []
    for match in re.finditer(token_pattern, code, re.VERBOSE | re.MULTILINE):
        token = match.group().strip()
        if token and not token.startswith(';'):
            tokens.append(token)

    return tokens


def parse(tokens):
    """Парсит токены в S-выражения"""

    def parse_expression(index):
        if index >= len(tokens):
            raise ValueError("Неожиданный конец выражения")

        token = tokens[index]

        if token == '(':
            # Парсим список
            index += 1
            elements = []

            while index < len(tokens) and tokens[index] != ')':
                expr, index = parse_expression(index)
                elements.append(expr)

            if index >= len(tokens):
                raise ValueError("Отсутствует закрывающая скобка")

            index += 1  # пропускаем ')'
            return tuple(elements), index

        elif token == ')':
            raise ValueError("Неожиданная закрывающая скобка")

        elif token.startswith('"') and token.endswith('"'):
            # Строка
            return {"type": "string", "value": token[1:-1]}, index + 1

        elif token.isdigit() or (token.startswith('-') and token[1:].isdigit()):
            # Целое число
            return int(token), index + 1

        elif '.' in token and token.replace('.', '').replace('-', '').isdigit():
            # Число с плавающей точкой
            return float(token), index + 1

        else:
            # Символ
            return token, index + 1

    if not tokens:
        return ()

    expr, _ = parse_expression(0)
    return expr
