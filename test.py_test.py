import unittest
from test import add

class TestAdd(unittest.TestCase):

    def test_positive_numbers(self):
        self.assertEqual(add(2, 3), 5)

    def test_negative_numbers(self):
        self.assertEqual(add(-1, -1), -2)

    def test_mixed_numbers(self):
        self.assertEqual(add(-1, 1), 0)

    def test_zero_first(self):
        self.assertEqual(add(0, 5), 5)

    def test_zero_second(self):
        self.assertEqual(add(5, 0), 5)

    def test_both_zero(self):
        self.assertEqual(add(0, 0), 0)

    def test_large_positive_numbers(self):
        self.assertEqual(add(10**6, 10**6), 2 * 10**6)

    def test_large_negative_numbers(self):
        self.assertEqual(add(-10**6, -10**6), -2 * 10**6)

    def test_float_numbers(self):
        self.assertAlmostEqual(add(0.1, 0.2), 0.3, places=7)

    def test_negative_float(self):
        self.assertAlmostEqual(add(-0.1, -0.2), -0.3, places=7)

    def test_mixed_float(self):
        self.assertAlmostEqual(add(-0.1, 0.2), 0.1, places=7)

    def test_zero_float(self):
        self.assertEqual(add(0.0, 0.0), 0.0)

    def test_very_small_float(self):
        self.assertAlmostEqual(add(1e-10, 2e-10), 3e-10, places=15)

    def test_very_large_float(self):
        self.assertAlmostEqual(add(1e10, 2e10), 3e10, places=0)

    def test_boolean_true_first(self):
        self.assertEqual(add(True, 1), 2)

    def test_boolean_true_second(self):
        self.assertEqual(add(1, True), 2)

    def test_both_boolean_true(self):
        self.assertEqual(add(True, True), 2)

    def test_boolean_false_first(self):
        self.assertEqual(add(False, 1), 1)

    def test_boolean_false_second(self):
        self.assertEqual(add(1, False), 1)

    def test_both_boolean_false(self):
        self.assertEqual(add(False, False), 0)

    def test_complex_numbers(self):
        self.assertEqual(add(1+2j, 3+4j), 4+6j)

    def test_complex_real_zero(self):
        self.assertEqual(add(0+2j, 3+0j), 3+2j)

    def test_string_concatenation(self):
        self.assertEqual(add("hello", "world"), "helloworld")

    def test_list_concatenation(self):
        self.assertEqual(add([1, 2], [3, 4]), [1, 2, 3, 4])

    def test_tuple_concatenation(self):
        self.assertEqual(add((1, 2), (3, 4)), (1, 2, 3, 4))

    def test_empty_list(self):
        self.assertEqual(add([], [1]), [1])

    def test_empty_tuple(self):
        self.assertEqual(add((), (1,)), (1,))

    def test_empty_string(self):
        self.assertEqual(add("", "test"), "test")

    def test_both_empty_string(self):
        self.assertEqual(add("", ""), "")

    def test_both_empty_list(self):
        self.assertEqual(add([], []), [])

    def test_both_empty_tuple(self):
        self.assertEqual(add((), ()), ())

    def test_string_number_type_error(self):
        with self.assertRaises(TypeError):
            add("a", 1)

    def test_list_number_type_error(self):
        with self.assertRaises(TypeError):
            add([1], 2)

    def test_dict_unsupported_type_error(self):
        with self.assertRaises(TypeError):
            add({}, {})

    def test_none_unsupported_type_error(self):
        with self.assertRaises(TypeError):
            add(None, 1)

    def test_none_both_unsupported_type_error(self):
        with self.assertRaises(TypeError):
            add(None, None)

if __name__ == '__main__':
    unittest.main()

    
