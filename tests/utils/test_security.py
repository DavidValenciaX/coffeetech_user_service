import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import unittest
import argon2
from unittest.mock import patch, MagicMock

from utils.security import hash_password, verify_password, ph


class TestSecurityFunctions(unittest.TestCase):
    """Test cases for the security module functions."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_password = "test_password_123"
        self.another_password = "another_password_456"
        self.empty_password = ""
        self.long_password = "a" * 1000  # Very long password
        self.special_chars_password = "p@ssw0rd!@#$%^&*()_+-=[]{}|;:'\",.<>?/~`"

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        result = hash_password(self.test_password)
        self.assertIsInstance(result, str)

    def test_hash_password_not_empty(self):
        """Test that hash_password returns a non-empty string."""
        result = hash_password(self.test_password)
        self.assertGreater(len(result), 0)

    def test_hash_password_different_each_time(self):
        """Test that hashing the same password produces different hashes (due to salt)."""
        hash1 = hash_password(self.test_password)
        hash2 = hash_password(self.test_password)
        
        # Hashes should be different due to random salt
        self.assertNotEqual(hash1, hash2)

    def test_hash_password_with_empty_string(self):
        """Test hashing an empty password."""
        result = hash_password(self.empty_password)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_hash_password_with_special_characters(self):
        """Test hashing a password with special characters."""
        result = hash_password(self.special_chars_password)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_hash_password_with_unicode(self):
        """Test hashing a password with unicode characters."""
        unicode_password = "pássw∅rd123µñíçødé"
        result = hash_password(unicode_password)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_hash_password_with_very_long_password(self):
        """Test hashing a very long password."""
        result = hash_password(self.long_password)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_hash_password_format(self):
        """Test that the hash has the expected Argon2 format."""
        result = hash_password(self.test_password)
        # Argon2 hashes start with $argon2id$
        self.assertTrue(result.startswith("$argon2"))

    def test_verify_password_correct_password(self):
        """Test password verification with correct password."""
        hashed = hash_password(self.test_password)
        result = verify_password(self.test_password, hashed)
        self.assertTrue(result)

    def test_verify_password_incorrect_password(self):
        """Test password verification with incorrect password."""
        hashed = hash_password(self.test_password)
        result = verify_password(self.another_password, hashed)
        self.assertFalse(result)

    def test_verify_password_empty_plain_password(self):
        """Test verification when plain password is empty."""
        hashed = hash_password(self.test_password)
        result = verify_password(self.empty_password, hashed)
        self.assertFalse(result)

    def test_verify_password_empty_hashed_password(self):
        """Test verification when hashed password is empty."""
        result = verify_password(self.test_password, self.empty_password)
        self.assertFalse(result)

    def test_verify_password_both_empty(self):
        """Test verification when both passwords are empty."""
        hashed = hash_password(self.empty_password)
        result = verify_password(self.empty_password, hashed)
        self.assertTrue(result)

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case sensitive."""
        hashed = hash_password("Password123")
        result = verify_password("password123", hashed)
        self.assertFalse(result)

    def test_verify_password_with_special_characters(self):
        """Test verification with special character passwords."""
        hashed = hash_password(self.special_chars_password)
        result = verify_password(self.special_chars_password, hashed)
        self.assertTrue(result)

    def test_verify_password_with_unicode(self):
        """Test verification with unicode character passwords."""
        unicode_password = "pássw∅rd123µñíçødé"
        hashed = hash_password(unicode_password)
        result = verify_password(unicode_password, hashed)
        self.assertTrue(result)

    def test_verify_password_invalid_hash_format(self):
        """Test verification with invalid hash format."""
        invalid_hash = "not_a_valid_hash"
        result = verify_password(self.test_password, invalid_hash)
        self.assertFalse(result)

    def test_verify_password_malformed_hash(self):
        """Test verification with malformed but argon2-like hash."""
        malformed_hash = "$argon2id$invalid$hash$format"
        result = verify_password(self.test_password, malformed_hash)
        self.assertFalse(result)

    def test_verify_password_with_very_long_password(self):
        """Test verification with very long password."""
        hashed = hash_password(self.long_password)
        result = verify_password(self.long_password, hashed)
        self.assertTrue(result)

    @patch('utils.security.ph')
    def test_hash_password_calls_argon2_hash(self, mock_ph):
        """Test that hash_password calls the Argon2 hasher correctly."""
        mock_ph.hash.return_value = "mocked_hash"
        
        result = hash_password(self.test_password)
        
        mock_ph.hash.assert_called_once_with(self.test_password)
        self.assertEqual(result, "mocked_hash")

    @patch('utils.security.ph')
    def test_verify_password_calls_argon2_verify_success(self, mock_ph):
        """Test that verify_password calls Argon2 verify correctly on success."""
        mock_ph.verify.return_value = None  # verify() returns None on success
        
        result = verify_password(self.test_password, "some_hash")
        
        mock_ph.verify.assert_called_once_with("some_hash", self.test_password)
        self.assertTrue(result)

    @patch('utils.security.ph')
    def test_verify_password_handles_verify_mismatch_error(self, mock_ph):
        """Test that verify_password handles VerifyMismatchError correctly."""
        mock_ph.verify.side_effect = argon2.exceptions.VerifyMismatchError()
        
        result = verify_password(self.test_password, "some_hash")
        
        mock_ph.verify.assert_called_once_with("some_hash", self.test_password)
        self.assertFalse(result)

    @patch('utils.security.ph')
    def test_verify_password_handles_invalid_hash_error(self, mock_ph):
        """Test that verify_password handles InvalidHash error correctly."""
        mock_ph.verify.side_effect = argon2.exceptions.InvalidHash()
        
        result = verify_password(self.test_password, "invalid_hash")
        
        mock_ph.verify.assert_called_once_with("invalid_hash", self.test_password)
        self.assertFalse(result)

    @patch('utils.security.ph')
    def test_verify_password_handles_unexpected_exception(self, mock_ph):
        """Test that verify_password propagates unexpected exceptions."""
        mock_ph.verify.side_effect = ValueError("Unexpected error")
        
        with self.assertRaises(ValueError):
            verify_password(self.test_password, "some_hash")

    def test_password_hasher_configuration(self):
        """Test that the password hasher is configured correctly."""
        # Check that ph is an Argon2 PasswordHasher instance
        self.assertIsInstance(ph, argon2.PasswordHasher)

    def test_integration_hash_and_verify_cycle(self):
        """Integration test for complete hash and verify cycle."""
        passwords_to_test = [
            "simple",
            "complex_P@ssw0rd!",
            "123456789",
            "",
            "a" * 100,
            "unicode_çhàrs_ñ_µ",
            "spaces in password",
            "tabs\tand\nnewlines",
        ]
        
        for password in passwords_to_test:
            with self.subTest(password=password[:20] + "..." if len(password) > 20 else password):
                # Hash the password
                hashed = hash_password(password)
                
                # Verify with correct password
                self.assertTrue(verify_password(password, hashed))
                
                # Verify with incorrect password (if not empty)
                if password:
                    wrong_password = password + "_wrong"
                    self.assertFalse(verify_password(wrong_password, hashed))

    def test_multiple_hash_verify_operations(self):
        """Test multiple hash and verify operations to ensure consistency."""
        for i in range(10):
            with self.subTest(iteration=i):
                test_password = f"test_password_{i}"
                hashed = hash_password(test_password)
                
                # Verify correct password
                self.assertTrue(verify_password(test_password, hashed))
                
                # Verify incorrect password
                wrong_password = f"wrong_password_{i}"
                self.assertFalse(verify_password(wrong_password, hashed))


if __name__ == '__main__':
    unittest.main()
