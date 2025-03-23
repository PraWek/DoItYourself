import unittest

from lisp import Interpreter, LispError, LispNameError, LispSyntaxError, Vector


class InterpreterTests(unittest.TestCase):
    def setUp(self):
        self.lisp = Interpreter()

    def evaluate(self, source):
        return self.lisp.execute(source)

    def test_arithmetic(self):
        self.assertEqual(self.evaluate("(+ 1 2 3)"), 6)
        self.assertEqual(self.evaluate("(*)"), 1)
        self.assertEqual(self.evaluate("(- 8 3 2)"), 3)
        self.assertEqual(self.evaluate("(- 4)"), -4)
        self.assertEqual(self.evaluate("(/ 24 3 2)"), 4)

    def test_numeric_errors_are_lisp_errors(self):
        for source in ('(+ 1 "two")', "(/ 1 0)", "(< 1)"):
            with self.subTest(source=source), self.assertRaises(LispError):
                self.evaluate(source)

    def test_comparisons_are_chained(self):
        self.assertIs(self.evaluate("(< 1 2 3)"), True)
        self.assertIs(self.evaluate("(< 1 3 2)"), False)
        self.assertIs(self.evaluate('(= "x" "x")'), True)

    def test_if_and_boolean_forms_are_lazy(self):
        self.assertEqual(self.evaluate("(if t 7 (/ 1 0))"), 7)
        self.assertEqual(self.evaluate("(and nil (/ 1 0))"), [])
        self.assertEqual(self.evaluate("(or 4 (/ 1 0))"), 4)

    def test_cond(self):
        source = "(cond ((> 2 3) 0) ((= 2 2) 1) (else 2))"
        self.assertEqual(self.evaluate(source), 1)
        self.assertEqual(self.evaluate("(cond ((> 2 3) 0))"), [])

    def test_define_and_set(self):
        self.assertEqual(self.evaluate("(define answer 40) (set! answer (+ answer 2)) answer"), 42)
        with self.assertRaises(LispNameError):
            self.evaluate("(set! missing 1)")
        self.assertEqual(self.evaluate("(set fresh 3) fresh"), 3)

    def test_lexical_closure(self):
        source = """
        (define (make-adder amount)
          (lambda (value) (+ value amount)))
        (define add-five (make-adder 5))
        (add-five 8)
        """
        self.assertEqual(self.evaluate(source), 13)

    def test_recursive_function(self):
        source = """
        (define (factorial n)
          (if (= n 0) 1 (* n (factorial (- n 1)))))
        (factorial 7)
        """
        self.assertEqual(self.evaluate(source), 5040)

    def test_lambda_arity(self):
        with self.assertRaises(LispError):
            self.evaluate("((lambda (x y) x) 1)")
        self.assertEqual(self.evaluate("((lambda (x &rest xs) (length xs)) 1 2 3)"), 2)

    def test_function_body_can_contain_several_expressions(self):
        source = "(define (step x) (+ x 1) (+ x 2)) (step 5)"
        self.assertEqual(self.evaluate(source), 7)

    def test_let_is_parallel_and_let_star_is_sequential(self):
        self.evaluate("(define x 10)")
        self.assertEqual(self.evaluate("(let ((x 1) (y x)) (+ x y))"), 11)
        self.assertEqual(self.evaluate("(let* ((x 1) (y x)) (+ x y))"), 2)
        self.assertEqual(self.evaluate("x"), 10)

    def test_quote_and_list_operations(self):
        self.assertEqual(self.evaluate("(car '(a b))"), "a")
        self.assertEqual(self.evaluate("(cdr '(a b))"), ["b"])
        self.assertEqual(self.evaluate("(cons 1 '(2 3))"), [1, 2, 3])
        self.assertEqual(self.evaluate("(append '(1) '(2 3))"), [1, 2, 3])
        self.assertIsInstance(self.evaluate("'[a b]"), Vector)

    def test_vectors_and_dicts(self):
        vector = self.evaluate("[1 (+ 1 1)]")
        self.assertIsInstance(vector, Vector)
        self.assertEqual(vector, [1, 2])
        self.assertEqual(self.evaluate('(get {"answer": 42} "answer")'), 42)
        self.assertEqual(self.evaluate('(get (dict "x" 3) "x")'), 3)

    def test_higher_order_functions(self):
        self.assertEqual(self.evaluate("(map (lambda (x) (* x 2)) '(1 2 3))"), [2, 4, 6])
        self.assertEqual(self.evaluate("(filter (lambda (x) (> x 1)) '(1 2 3))"), [2, 3])
        self.assertEqual(self.evaluate("(reduce + '(1 2 3) 10)"), 16)
        self.assertEqual(self.evaluate("(apply + '(1 2 3))"), 6)

    def test_try_receives_error(self):
        self.assertEqual(self.evaluate("(try (/ 1 0) 17)"), 17)
        self.assertIn("деление", self.evaluate("(try (/ 1 0) error)"))
        self.assertEqual(self.evaluate("(try (/ 1 0) (lambda (message) (length message)))"), 18)

    def test_progn_returns_last_value(self):
        self.assertEqual(self.evaluate("(progn 1 2 3)"), 3)

    def test_string_and_symbol_are_distinct(self):
        self.assertEqual(self.evaluate('"name"'), "name")
        self.assertIs(self.evaluate('(string? "name")'), True)
        self.assertIs(self.evaluate("(symbol? 'name)"), True)
        self.assertIs(self.evaluate("(string? 'name)"), False)
        with self.assertRaises(LispNameError):
            self.evaluate("name")

    def test_malformed_forms(self):
        for source in (
            "(if 1)",
            "(define 1 2)",
            "(let (x 1) x)",
            "(let ((x 1) (x 2)) x)",
            "(lambda (x x) x)",
        ):
            with self.subTest(source=source), self.assertRaises((LispError, LispSyntaxError)):
                self.evaluate(source)

    def test_format(self):
        self.assertEqual(self.lisp.format([]), "nil")
        self.assertEqual(self.lisp.format(True), "t")
        self.assertEqual(self.lisp.format([1, "два"]), '(1 "два")')


if __name__ == "__main__":
    unittest.main()
