"""
задание:
написать функции для работы с пространством имён
1. принимает список словарей / мап и добавляет пустую в конец (создание нового скоупа, для let)
2. принимает список словарей, ключ и значение и присваивает значение в текущей мапе (самой вложенной)
3. принимает список словарей и ключ и возвращает его значение, делая поиск начиная с самой вложенной мапы
"""

def append_value(struct):
    struct.append({})
    return struct

struct = [{"a": 1}]
print(append_value(struct))


def change_value(struct, changing_key, changing_val):
    struct[-1][changing_key] = changing_val
    return struct

struct = [{"a": 1}]
changing_key = "a"
changing_val = 2
print(change_value(struct, changing_key, changing_val))


def find_value_by_key(list_of_dicts, key):
    values = []
    for dictionary in reversed(list_of_dicts):
        if key in dictionary:
            values.append(dictionary[key])
    return values

struct = [{"a": 1}]
key = "a"
print(*find_value_by_key(struct, key))
