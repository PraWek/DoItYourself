import unittest

from lisp import DictLiteral, LispSyntaxError, Symbol, VectorLiteral, parse, parse_many, tokenize


class ParserTests(unittest.TestCase):
    def test_tokenize_strings_comments_and_quote(self):
        source = '(list "a b" \'name) ; comment\n# old comment\n(+ 1 2)'
        self.assertEqual(
            tokenize(source),
            ["(", "list", '"a b"', "'", "name", ")", "(", "+", "1", "2", ")"],
        )

    def test_parse_expression(self):
        self.assertEqual(parse("(+ 1 (* 2 3))"), [Symbol("+"), 1, [Symbol("*"), 2, 3]])

    def test_parse_all_numeric_forms(self):
        self.assertEqual(parse("(list -2 3.5 1e2)"), [Symbol("list"), -2, 3.5, 100.0])

    def test_parse_quote(self):
        self.assertEqual(parse("'(a 1)"), [Symbol("quote"), [Symbol("a"), 1]])

    def test_parse_vector_and_dict(self):
        vector = parse('[1 "two"]')
        mapping = parse('{"a": 1 "b", 2}')
        self.assertIsInstance(vector, VectorLiteral)
        self.assertEqual(vector.values, (1, "two"))
        self.assertIsInstance(mapping, DictLiteral)
        self.assertEqual(mapping.pairs, (("a", 1), ("b", 2)))

    def test_parse_many(self):
        self.assertEqual(len(parse_many("(define x 1)\n(+ x 2)")), 2)

    def test_reject_trailing_expression(self):
        with self.assertRaises(LispSyntaxError):
            parse("1 2")

    def test_reject_unbalanced_input(self):
        for source in ("(+ 1 2", "(+ 1 2))", '"open'):
            with self.subTest(source=source), self.assertRaises(LispSyntaxError):
                parse(source)

    def test_empty_single_parse_is_an_error(self):
        with self.assertRaises(LispSyntaxError):
            parse(" ; nothing")


if __name__ == "__main__":
    unittest.main()
