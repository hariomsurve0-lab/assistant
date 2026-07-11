import unittest
from jarvis.core.processor import process_command

class TestProcessor(unittest.TestCase):
    def test_greetings(self):
        res = process_command("Namaste Jarvis")
        self.assertTrue(any(x in res for x in ["Namaste", "Swagat", "Hazir", "sewa"]))

    def test_jokes(self):
        res = process_command("Joke sunao")
        self.assertTrue("exam" in res or "doctor" in res or "Teacher" in res or "Pappu" in res or "doctor" in res)

    def test_motivation(self):
        res = process_command("motivate")
        self.assertTrue(any(x in res for x in ["tension", "best", "pankho", "Gopal", "todenge"]))

if __name__ == "__main__":
    unittest.main()
