import unittest
from jarvis.tts.manager import convert_numbers_to_hindi

class TestNumConversion(unittest.TestCase):
    def test_single_digits(self):
        self.assertEqual(convert_numbers_to_hindi("1"), "एक")
        self.assertEqual(convert_numbers_to_hindi("5"), "पाँच")
        self.assertEqual(convert_numbers_to_hindi("9"), "नौ")

    def test_double_digits(self):
        self.assertEqual(convert_numbers_to_hindi("26"), "छब्बीस")
        self.assertEqual(convert_numbers_to_hindi("99"), "निन्यानवे")

    def test_large_numbers(self):
        self.assertEqual(convert_numbers_to_hindi("2026"), "दो हज़ार छब्बीस")
        self.assertEqual(convert_numbers_to_hindi("1500"), "एक हज़ार पाँच सौ")

    def test_embedded_numbers(self):
        self.assertEqual(
            convert_numbers_to_hindi("Sir, aaj 11 July hai."),
            "Sir, aaj ग्यारह July hai."
        )
        # Note: 11 is 'ग्यारह' or 'इ्यारह' depending on spelling map. Let's assert based on our _HINDI_ONES map.
        # Let's check _HINDI_ONES map: 11 is 'ग्यारह'
        self.assertEqual(
            convert_numbers_to_hindi("Sir, aaj 11 hai."),
            "Sir, aaj ग्यारह hai."
        )

if __name__ == "__main__":
    unittest.main()
