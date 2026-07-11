import unittest
from jarvis.config import encrypt_secret, decrypt_secret

class TestConfigEncryption(unittest.TestCase):
    def test_encrypt_decrypt(self):
        plain = "my_super_secret_api_key_123"
        encrypted = encrypt_secret(plain)
        
        # Ensure it is not stored plain
        self.assertNotEqual(plain, encrypted)
        
        decrypted = decrypt_secret(encrypted)
        # Ensure it matches initial secret
        self.assertEqual(plain, decrypted)

    def test_empty_secret(self):
        self.assertEqual(encrypt_secret(""), "")
        self.assertEqual(decrypt_secret(""), "")

if __name__ == "__main__":
    unittest.main()
