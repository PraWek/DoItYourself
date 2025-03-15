from evaluate import evaluate


def append_value(struct):
    if not isinstance(struct, list):
        raise TypeError("Пространство имён должно быть списком")
    struct.append({})
    return struct


def change_value(struct, changing_key, changing_val):
    if not isinstance(struct, list) or not struct:
        raise ValueError("Некорректное пространство имён")
    if not isinstance(changing_key, str):
        raise TypeError("Ключ должен быть строкой")
    struct[-1][changing_key] = changing_val
    return struct


def my_set(expression, namespaces):
    try:
        if not isinstance(expression, tuple) or len(expression) != 2:
            raise ValueError("Некорректная структура выражения set")

        variable_name, value_tuple = expression
        if not isinstance(variable_name, str):
            raise TypeError("Имя переменной должно быть строкой")

        if not isinstance(value_tuple, tuple) or len(value_tuple) != 2:
            raise ValueError("Некорректная структура значения")

        value, _ = value_tuple
        evaluated_value = evaluate(value, namespaces)
        change_value(namespaces, variable_name, evaluated_value)
        return namespaces
    except Exception as e:
        raise ValueError(f"Ошибка в операции set: {str(e)}")


def let(expression, namespaces):
    try:
        if not isinstance(expression, tuple) or len(expression) != 2:
            raise ValueError("Некорректная структура выражения let")

        bindings, body = expression
        if not isinstance(bindings, tuple):
            raise TypeError("Привязки должны быть кортежем")

        namespaces = append_value(namespaces)

        for binding in bindings:
            if not isinstance(binding, tuple) or len(binding) != 2:
                raise ValueError("Некорректная структура привязки")

            var_name, value_tuple = binding
            if not isinstance(var_name, str):
                raise TypeError("Имя переменной должно быть строкой")

            if not isinstance(value_tuple, tuple) or len(value_tuple) != 2:
                raise ValueError("Некорректная структура значения в привязке")

            value, _ = value_tuple
            evaluated_value = evaluate(value, namespaces)
            change_value(namespaces, var_name, evaluated_value)

        result = evaluate(body, namespaces)
        namespaces.pop()
        return result
    except Exception as e:
        if isinstance(e, (ValueError, TypeError)):
            raise
        raise ValueError(f"Ошибка в операции let: {str(e)}")
