import unittest
from file_manager import FileManager


class TestSimpleFileManager(unittest.TestCase):
    def test_sanitize_filename(self):
        """Test that the sanitize_filename method correctly replaces invalid characters."""
        # Test with a filename containing invalid characters
        dirty_filename = "test:file*with?invalid<chars>|"
        clean_filename = FileManager.sanitize_filename(dirty_filename)
        expected = "test_file_with_invalid_chars_"
        self.assertEqual(clean_filename, expected)

    def test_sanitize_filename_with_normal_name(self):
        """Test that the sanitize_filename method doesn't change valid filenames."""
        # Test with a normal filename
        normal_filename = "normal_filename.txt"
        result = FileManager.sanitize_filename(normal_filename)
        self.assertEqual(result, normal_filename)


if __name__ == "__main__":
    unittest.main()
