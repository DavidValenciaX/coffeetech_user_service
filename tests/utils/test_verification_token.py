import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import unittest
import string
import re
from unittest.mock import patch

from utils.verification_token import generate_verification_token


class TestGenerateVerificationToken(unittest.TestCase):
    """Test cases for the generate_verification_token function."""

    def test_default_length(self):
        """Test that the default token length is 3."""
        token = generate_verification_token()
        self.assertEqual(len(token), 3)

    def test_custom_length(self):
        """Test token generation with custom lengths."""
        # Test various lengths
        test_lengths = [1, 5, 10, 20, 50]
        for length in test_lengths:
            with self.subTest(length=length):
                token = generate_verification_token(length)
                self.assertEqual(len(token), length)

    def test_zero_length(self):
        """Test token generation with zero length."""
        token = generate_verification_token(0)
        self.assertEqual(len(token), 0)
        self.assertEqual(token, "")

    def test_negative_length(self):
        """Test token generation with negative length."""
        # According to Python's random.choices behavior, negative k returns empty list
        token = generate_verification_token(-1)
        self.assertEqual(len(token), 0)
        self.assertEqual(token, "")

    def test_token_contains_valid_characters(self):
        """Test that generated tokens only contain valid characters."""
        valid_chars = string.ascii_letters + string.digits
        
        # Test multiple tokens to ensure consistency
        for _ in range(100):
            token = generate_verification_token(10)
            for char in token:
                self.assertIn(char, valid_chars, 
                            f"Invalid character '{char}' found in token '{token}'")

    def test_token_format_pattern(self):
        """Test that generated tokens match the expected pattern."""
        # Pattern: only alphanumeric characters
        pattern = re.compile(r'^[a-zA-Z0-9]*$')
        
        for _ in range(50):
            token = generate_verification_token(8)
            self.assertTrue(pattern.match(token), 
                          f"Token '{token}' doesn't match expected pattern")

    def test_randomness(self):
        """Test that generated tokens are random (not always the same)."""
        tokens = set()
        
        # Generate multiple tokens and check they're not all identical
        for _ in range(100):
            token = generate_verification_token(6)
            tokens.add(token)
        
        # With 6 characters from 62 possible chars, we should get variety
        # (though theoretically they could be the same, it's extremely unlikely)
        self.assertGreater(len(tokens), 1, 
                          "All generated tokens are identical - randomness issue")

    def test_multiple_calls_return_strings(self):
        """Test that multiple calls consistently return string objects."""
        for length in [1, 3, 5, 10]:
            with self.subTest(length=length):
                token = generate_verification_token(length)
                self.assertIsInstance(token, str)

    def test_large_length(self):
        """Test token generation with a large length."""
        large_length = 1000
        token = generate_verification_token(large_length)
        self.assertEqual(len(token), large_length)
        self.assertIsInstance(token, str)

    @patch('utils.verification_token.random.choices')
    def test_random_choices_called_correctly(self, mock_choices):
        """Test that random.choices is called with correct parameters."""
        mock_choices.return_value = ['a', 'b', 'c']
        
        generate_verification_token(3)
        
        # Verify random.choices was called with correct arguments
        expected_chars = string.ascii_letters + string.digits
        mock_choices.assert_called_once_with(expected_chars, k=3)

    @patch('utils.verification_token.random.choices')
    def test_random_choices_return_value_handling(self, mock_choices):
        """Test that the function correctly joins the result from random.choices."""
        mock_choices.return_value = ['X', 'Y', 'Z']
        
        result = generate_verification_token(3)
        
        self.assertEqual(result, 'XYZ')

    def test_character_distribution(self):
        """Test that both letters and digits can appear in tokens."""
        # Generate many tokens to check we get both letters and digits
        all_chars = set()
        
        for _ in range(1000):
            token = generate_verification_token(10)
            all_chars.update(token)
        
        # Check we have at least some letters and some digits
        has_letters = any(c.isalpha() for c in all_chars)
        has_digits = any(c.isdigit() for c in all_chars)
        
        self.assertTrue(has_letters, "No letters found in generated tokens")
        self.assertTrue(has_digits, "No digits found in generated tokens")

    def test_case_sensitivity(self):
        """Test that both uppercase and lowercase letters can appear."""
        all_chars = set()
        
        for _ in range(1000):
            token = generate_verification_token(10)
            all_chars.update(token)
        
        # Check for both cases
        has_uppercase = any(c.isupper() for c in all_chars)
        has_lowercase = any(c.islower() for c in all_chars)
        
        self.assertTrue(has_uppercase, "No uppercase letters found in generated tokens")
        self.assertTrue(has_lowercase, "No lowercase letters found in generated tokens")


if __name__ == '__main__':
    unittest.main()
