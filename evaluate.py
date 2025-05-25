def find_value_by_key(names, key):
    for namespace in names:
        if key in namespace:
            return namespace[key]
    return None


def evaluate_elems(values, names):
    if not values:
        return ()
    if isinstance(values, tuple) and len(values) == 2:
        head, tail = values
        return (evaluate(head, names), evaluate_elems(tail, names))
    else:
        return (evaluate(values, names), ())


def evaluate(value, names):
    try:
        if isinstance(value, (int, float)):
            return value

        elif isinstance(value, dict) and "type" in value:
            if value["type"] == "string":
                return value
            elif value["type"] == "array":
                return {"type": "array", "value": [evaluate(x, names) for x in value["value"]]}
            elif value["type"] == "dict":
                return {"type": "dict", "value": {k: evaluate(v, names) for k, v in value["value"].items()}}

        elif isinstance(value, str):
            if not names:
                raise ValueError("Пустое пространство имён")
            res = find_value_by_key(names, value)
            if res is not None:
                return res
            raise NameError(f"Неопределённая переменная: '{value}'")

        elif isinstance(value, dict):
            if not value:
                raise ValueError("Пустой словарь")
            return value

        elif isinstance(value, tuple):
            if not value and value != ():
                raise ValueError("Некорректный кортеж")
            if not value:
                return value

            if len(value) < 1:
                raise ValueError("Некорректная структура кортежа")

            if len(value) < 2:
                head = value[0]
                tail = ()
            else:
                head, tail = value[0], value[1:]

            try:
                head = evaluate(head, names)
            except Exception as e:
                raise ValueError(f"Ошибка при вычислении головы выражения: {str(e)}")

            if not isinstance(head, dict):
                raise TypeError(f"Выражение '{value}' не является вызовом функции")

            if "macro" in head:
                try:
                    macro = head["macro"]
                    return macro(tail)
                except Exception as e:
                    raise ValueError(f"Ошибка при выполнении макроса: {str(e)}")
            elif "function" in head:
                try:
                    func = head["function"]
                    tail = evaluate_elems(tail, names)
                    return func(tail)
                except Exception as e:
                    raise ValueError(f"Ошибка при выполнении функции: {str(e)}")
            raise SystemError(f"Неожиданный тип словаря: '{value}'")

        raise TypeError(f"Неподдерживаемый тип данных: '{type(value)}'")
    except Exception as e:
        if isinstance(e, (ValueError, TypeError, NameError, SystemError)):
            raise
        raise ValueError(f"Ошибка при вычислении выражения: {str(e)}")