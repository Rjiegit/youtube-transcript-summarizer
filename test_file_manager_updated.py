import unittest
import os
import glob
import tempfile
from unittest.mock import Mock, patch
from file_manager import FileManager

class TestFileManager(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a mock config
        self.mock_config = Mock()
        self.mock_config.data_dir = 'data/test'
        self.mock_config.summarized_dir = 'data/test/_summarized'

        # Create a file manager with the mock config
        self.file_manager = FileManager(config=self.mock_config)

        # Ensure test directories exist
        os.makedirs(self.mock_config.data_dir, exist_ok=True)
        os.makedirs(self.mock_config.summarized_dir, exist_ok=True)

    def tearDown(self):
        """Clean up after each test method."""
        # Remove test files and directories
        for pattern in ['data/test/*.txt', 'data/test/_summarized/*.md']:
            for file_path in glob.glob(pattern):
                if os.path.isfile(file_path):
                    os.remove(file_path)

    def test_sanitize_filename(self):
        """Test that sanitize_filename correctly replaces invalid characters."""
        # Test with a filename containing invalid characters
        dirty_filename = 'test:file*with?invalid<chars>|'
        clean_filename = self.file_manager.sanitize_filename(dirty_filename)
        expected = 'test_file_with_invalid_chars__'
        self.assertEqual(clean_filename, expected)

        # Test with a normal filename
        normal_filename = 'normal_filename.txt'
        result = self.file_manager.sanitize_filename(normal_filename)
        self.assertEqual(result, normal_filename)

    def test_save_text_relative_path(self):
        """Test saving text to a file with a relative path."""
        # Test data
        test_text = 'This is a test content.'
        test_file = 'test_output.txt'

        # Save the text
        full_path = self.file_manager.save_text(test_text, test_file)

        # Check if the file exists and has the correct content
        self.assertTrue(os.path.exists(full_path))

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertEqual(content, test_text)

    def test_save_text_absolute_path(self):
        """Test saving text to a file with an absolute path."""
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test data
            test_text = 'This is a test content with absolute path.'
            test_file = os.path.join(temp_dir, 'test_output_abs.txt')

            # Save the text
            full_path = self.file_manager.save_text(test_text, test_file)

            # Check if the file exists and has the correct content
            self.assertTrue(os.path.exists(full_path))

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.assertEqual(content, test_text)

    def test_delete_file(self):
        """Test deleting a file."""
        # Create a temporary file
        test_file = os.path.join(self.mock_config.data_dir, 'temp_file.txt')

        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('Temporary file content')

        # Test deleting the file
        self.assertTrue(os.path.exists(test_file))
        self.file_manager.delete_file(test_file)
        self.assertFalse(os.path.exists(test_file))

    def test_delete_nonexistent_file(self):
        """Test deleting a file that doesn't exist."""
        # This should not raise an exception
        nonexistent_file = os.path.join(self.mock_config.data_dir, 'nonexistent_file.txt')
        self.file_manager.delete_file(nonexistent_file)

    @patch('glob.glob')
    def test_delete_zone_identifier_files(self, mock_glob):
        """Test deleting Zone.Identifier files."""
        # Mock the glob.glob function to return a list of Zone.Identifier files
        mock_files = [
            os.path.join(self.mock_config.data_dir, 'file1:Zone.Identifier'),
            os.path.join(self.mock_config.data_dir, 'file2:Zone.Identifier')
        ]
        mock_glob.return_value = mock_files

        # Create a spy on the delete_file method
        with patch.object(self.file_manager, 'delete_file', wraps=self.file_manager.delete_file) as spy_delete_file:
            # Call the method under test
            self.file_manager.delete_zone_identifier_files(self.mock_config.data_dir)

            # Verify that delete_file was called for each Zone.Identifier file
            self.assertEqual(spy_delete_file.call_count, len(mock_files))
            for file_path in mock_files:
                spy_delete_file.assert_any_call(file_path)

    @patch('glob.glob')
    def test_get_files_to_process(self, mock_glob):
        """Test getting files to process."""
        # Mock the glob.glob function to return different lists for different patterns
        def side_effect(pattern):
            if pattern.endswith('*.mp3'):
                return ['data/videos/file1.mp3']
            elif pattern.endswith('*.mp4'):
                return ['data/videos/file2.mp4']
            elif pattern.endswith('*.m4a'):
                return ['data/videos/file3.m4a']
            elif pattern.endswith('*.webm'):
                return ['data/videos/file4.webm']
            return []

        mock_glob.side_effect = side_effect

        # Call the method under test
        files = self.file_manager.get_files_to_process()

        # Verify the result
        expected = [
            'data/videos/file1.mp3',
            'data/videos/file2.mp4',
            'data/videos/file3.m4a',
            'data/videos/file4.webm'
        ]
        self.assertEqual(files, expected)

    @patch('glob.glob')
    def test_get_files_to_process_with_custom_patterns(self, mock_glob):
        """Test getting files to process with custom patterns."""
        # Mock the glob.glob function to return different lists for different patterns
        def side_effect(pattern):
            if pattern == 'data/custom/*.txt':
                return ['data/custom/file1.txt', 'data/custom/file2.txt']
            elif pattern == 'data/custom/*.csv':
                return ['data/custom/file3.csv']
            return []

        mock_glob.side_effect = side_effect

        # Call the method under test with custom patterns
        custom_patterns = ['data/custom/*.txt', 'data/custom/*.csv']
        files = self.file_manager.get_files_to_process(patterns=custom_patterns)

        # Verify the result
        expected = [
            'data/custom/file1.txt',
            'data/custom/file2.txt',
            'data/custom/file3.csv'
        ]
        self.assertEqual(files, expected)

if __name__ == '__main__':
    unittest.main()
