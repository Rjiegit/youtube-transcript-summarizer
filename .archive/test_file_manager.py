import unittest
import os
import tempfile
from file_manager import FileManager


class TestFileManager(unittest.TestCase):
    def test_sanitize_filename(self):
        # Test sanitizing filenames with invalid characters
        dirty_filename = "test/file:with*invalid?chars<>|"
        clean_filename = FileManager.sanitize_filename(dirty_filename)
        expected = "test_file_with_invalid_chars___"
        self.assertEqual(clean_filename, expected)

    def test_save_text(self):
        # Create a temporary test directory
        test_dir = "data/test"
        os.makedirs(test_dir, exist_ok=True)

        # Test saving text to a file
        test_text = "This is a test content."
        test_file = "test_output.txt"

        try:
            FileManager.save_text(test_text, f"test/{test_file}")

            # Check if the file exists and has the correct content
            full_path = f"data/test_{test_file}"
            self.assertTrue(os.path.exists(full_path))

            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertEqual(content, test_text)
        finally:
            # Clean up
            if os.path.exists(f"data/test_{test_file}"):
                os.remove(f"data/test_{test_file}")

    def test_delete_file(self):
        # Create a temporary file
        test_dir = "data/test"
        os.makedirs(test_dir, exist_ok=True)
        test_file = f"{test_dir}/temp_file.txt"

        with open(test_file, "w", encoding="utf-8") as f:
            f.write("Temporary file content")

        # Test deleting the file
        self.assertTrue(os.path.exists(test_file))
        FileManager.delete_file(test_file)
        self.assertFalse(os.path.exists(test_file))


if __name__ == "__main__":
    unittest.main()
