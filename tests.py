import unittest
from all_namespace import namespace
from tokenize_and_parse import tokenize, parse
from evaluate import evaluate
from calculation_functions import add, subtract, multiply, divide
from comparison_functions import less_than, greater_than, less_or_equal, greater_or_equal, equal


class TestLispInterpreter(unittest.TestCase):
    def setUp(self):
        self.names = namespace()

    def test_arithmetic(self):
        # Тест сложения
        self.assertEqual(add((5, (3, ()))), 8)
        self.assertEqual(add((1, (2, (3, ())))), 6)
        self.assertEqual(add(()), 0)

        # Тест вычитания
        self.assertEqual(subtract((5, (3, ()))), 2)
        with self.assertRaises(ValueError):
            subtract((1,))

        # Тест умножения
        self.assertEqual(multiply((4, (2, ()))), 8)
        self.assertEqual(multiply((2, (3, (2, ())))), 12)
        self.assertEqual(multiply(()), 1)

        # Тест деления
        self.assertEqual(divide((10, (2, ()))), 5)
        with self.assertRaises(ValueError):
            divide((1, (0, ())))

    def test_comparison(self):
        # Тест сравнений
        self.assertEqual(less_than((3, (5, ()))), 1)
        self.assertEqual(less_than((5, (3, ()))), ())

        self.assertEqual(greater_than((5, (3, ()))), 1)
        self.assertEqual(greater_than((3, (5, ()))), ())

        self.assertEqual(less_or_equal((3, (3, ()))), 1)
        self.assertEqual(less_or_equal((5, (3, ()))), ())

        self.assertEqual(greater_or_equal((3, (3, ()))), 1)
        self.assertEqual(greater_or_equal((2, (3, ()))), ())

        self.assertEqual(equal((3, (3, ()))), 1)
        self.assertEqual(equal((2, (3, ()))), ())

    def test_tokenize_and_parse(self):
        # Тест токенизации
        tokens = tokenize('(+ 1 2)')
        self.assertEqual(tokens, ['(', '+', '1', '2', ')'])

        # Тест парсинга
        parsed = parse(['(', '+', '1', '2', ')'])
        self.assertEqual(parsed, ('+', (1, 2)))

    def test_data_types(self):
        # Тест строк
        expr = '"Hello, World!"'
        tokens = tokenize(expr)
        parsed = parse(tokens)
        self.assertEqual(parsed, {"type": "string", "value": "Hello, World!"})

        # Тест массивов
        expr = '[ 1 2 3 ]'
        tokens = tokenize(expr)
        parsed = parse(tokens)
        self.assertEqual(parsed, {"type": "array", "value": [1, 2, 3]})

        # Тест словарей
        # expr = '{ "a" : 1, "b" : 2 }'
        # tokens = tokenize(expr)
        # parsed = parse(tokens)
        # expected = {
        #     "type": "dict",
        #     "value": {
        #         "a": 1,
        #         "b": 2
        #     }
        # }
        # self.assertEqual(parsed, expected)

        # parsed_dict = parsed["value"]
        # self.assertEqual(len(parsed_dict), 2)
        # for key_dict, value in parsed_dict.items():
        #     self.assertEqual(key_dict["type"], "string")
        #     key = key_dict["value"]
        #     if key == "a":
        #         self.assertEqual(value, 1)
        #     elif key == "b":
        #         self.assertEqual(value, 2)

    def test_evaluate(self):
        # Тест вычисления выражений
        expr = ('+', (1, (2, ())))
        result = evaluate(expr, self.names)
        self.assertEqual(result, 3)

        # Тест обработки ошибок
        with self.assertRaises(ValueError):
            evaluate(('/', (1, (0, ()))), self.names)


if __name__ == '__main__':
    unittest.main()
