from llm_client import test_file
test_file_example="""
import unittest
from input import add

class TestAdd(unittest.TestCase):

    def test_positive_numbers(self):
        self.assertEqual(add(2, 3), 5)

    def test_negative_numbers(self):
        self.assertEqual(add(-1, -1), -2)

    def test_mixed_numbers(self):
        self.assertEqual(add(-1, 1), 0)

if __name__ == '__main__':
    unittest.main()
"""

def generate_py_file(file_function:str):
    try:
        with open(file_function,"r", encoding="utf-8") as f:
            extract_text= f.read()
        prompt=f"""
                you are a  python unittest builder that uses unittest library 
                to generate a test file for a {extract_text}
                the output must return tests file only:
                . with the unit test only as example{test_file_example}
                • no explanation
                • no markdown
                • no commentary
                • no extra text
                and make a tests including all the edge cases 
                and every posible case you can think of, and make sure to cover all the lines of the code
                and the file is came form{file_function}.py file 
                """
    except FileNotFoundError:
        print(f"Error: The file '{file_function}' was not found.")
        return
    test_file(prompt, file_function)



