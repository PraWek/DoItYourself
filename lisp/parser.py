import json
from dataclasses import dataclass
from typing import Iterable

from .errors import LispSyntaxError


class Symbol(str):
    pass


class Vector(list):
    pass


@dataclass(frozen=True)
class VectorLiteral:
    values: tuple


@dataclass(frozen=True)
class DictLiteral:
    pairs: tuple


DELIMITERS = "()[]{}':,"


def tokenize(source: str) -> list[str]:
    if not isinstance(source, str):
        raise TypeError("Исходный код должен быть строкой")

    tokens = []
    index = 0
    while index < len(source):
        char = source[index]

        if char.isspace() or char == ",":
            index += 1
            continue

        if char in ";#":
            newline = source.find("\n", index)
            index = len(source) if newline == -1 else newline + 1
            continue

        if char in "()[]{}':":
            tokens.append(char)
            index += 1
            continue

        if char == '"':
            start = index
            index += 1
            escaped = False
            while index < len(source):
                current = source[index]
                if current == '"' and not escaped:
                    index += 1
                    tokens.append(source[start:index])
                    break
                if current == "\n" and not escaped:
                    raise LispSyntaxError("Строка не закрыта до конца строки")
                escaped = current == "\\" and not escaped
                if current != "\\":
                    escaped = False
                index += 1
            else:
                raise LispSyntaxError("Незакрытая строка")
            continue

        start = index
        while index < len(source):
            current = source[index]
            if current.isspace() or current in DELIMITERS or current in ";#":
                break
            index += 1
        tokens.append(source[start:index])

    return tokens


def _atom(token: str):
    if token.startswith('"'):
        try:
            return json.loads(token)
        except json.JSONDecodeError as error:
            raise LispSyntaxError(f"Некорректная строка: {error.msg}") from error

    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return Symbol(token)


class _Reader:
    def __init__(self, tokens: Iterable[str]):
        self.tokens = list(tokens)
        self.index = 0

    def read(self):
        if self.index >= len(self.tokens):
            raise LispSyntaxError("Неожиданный конец выражения")

        token = self.tokens[self.index]
        self.index += 1

        if token == "(":
            return self._read_sequence(")", list)
        if token == "[":
            return VectorLiteral(tuple(self._read_sequence("]", list)))
        if token == "{":
            return self._read_dict()
        if token == "'":
            return [Symbol("quote"), self.read()]
        if token in (")", "]", "}"):
            raise LispSyntaxError(f"Неожиданная закрывающая скобка: {token}")
        if token == ":":
            raise LispSyntaxError("Неожиданное двоеточие")
        return _atom(token)

    def _read_sequence(self, closing: str, factory):
        values = []
        while self.index < len(self.tokens) and self.tokens[self.index] != closing:
            values.append(self.read())
        if self.index >= len(self.tokens):
            raise LispSyntaxError(f"Отсутствует закрывающая скобка {closing}")
        self.index += 1
        return factory(values)

    def _read_dict(self):
        pairs = []
        while self.index < len(self.tokens) and self.tokens[self.index] != "}":
            key = self.read()
            if self.index < len(self.tokens) and self.tokens[self.index] == ":":
                self.index += 1
            if self.index >= len(self.tokens) or self.tokens[self.index] == "}":
                raise LispSyntaxError("У ключа словаря отсутствует значение")
            pairs.append((key, self.read()))
        if self.index >= len(self.tokens):
            raise LispSyntaxError("Отсутствует закрывающая скобка }")
        self.index += 1
        return DictLiteral(tuple(pairs))


def parse(tokens_or_source):
    tokens = tokenize(tokens_or_source) if isinstance(tokens_or_source, str) else list(tokens_or_source)
    if not tokens:
        raise LispSyntaxError("Пустой ввод")
    reader = _Reader(tokens)
    expression = reader.read()
    if reader.index != len(tokens):
        raise LispSyntaxError("После выражения остались лишние токены")
    return expression


def parse_many(tokens_or_source) -> list:
    tokens = tokenize(tokens_or_source) if isinstance(tokens_or_source, str) else list(tokens_or_source)
    reader = _Reader(tokens)
    expressions = []
    while reader.index < len(tokens):
        expressions.append(reader.read())
    return expressions
