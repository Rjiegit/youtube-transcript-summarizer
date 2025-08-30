import unittest
from unittest.mock import Mock, patch
import os
from main import Main


class TestMain(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create mock objects for dependencies
        self.mock_config = Mock()
        self.mock_config.timezone = unittest.mock.ANY
        self.mock_config.file_patterns = ["pattern1", "pattern2"]

        self.mock_transcriber = Mock()
        self.mock_summarizer = Mock()
        self.mock_file_manager = Mock()
        self.mock_summary_storage = Mock()
        self.mock_processor = Mock()

        # Create a Main instance with mock dependencies
        self.main = Main(
            config=self.mock_config,
            transcriber=self.mock_transcriber,
            summarizer=self.mock_summarizer,
            file_manager=self.mock_file_manager,
            summary_storage=self.mock_summary_storage,
            processor=self.mock_processor,
        )

    def test_init(self):
        """Test initializing the Main class with dependencies."""
        # Verify that the dependencies were set correctly
        self.assertEqual(self.main.config, self.mock_config)
        self.assertEqual(self.main.transcriber, self.mock_transcriber)
        self.assertEqual(self.main.summarizer, self.mock_summarizer)
        self.assertEqual(self.main.file_manager, self.mock_file_manager)
        self.assertEqual(self.main.summary_storage, self.mock_summary_storage)
        self.assertEqual(self.main.processor, self.mock_processor)

        # Verify that validate was called on the config
        self.mock_config.validate.assert_called_once()

    @patch("main.Config")
    @patch("main.Transcriber")
    @patch("main.Summarizer")
    @patch("main.FileManager")
    @patch("main.SummaryStorage")
    @patch("main.Processor")
    def test_init_without_dependencies(
        self,
        mock_processor_class,
        mock_summary_storage_class,
        mock_file_manager_class,
        mock_summarizer_class,
        mock_transcriber_class,
        mock_config_class,
    ):
        """Test initializing the Main class without dependencies."""
        # Configure the mocks
        mock_config = Mock()
        mock_config_class.return_value = mock_config

        mock_transcriber = Mock()
        mock_transcriber_class.return_value = mock_transcriber

        mock_summarizer = Mock()
        mock_summarizer_class.return_value = mock_summarizer

        mock_file_manager = Mock()
        mock_file_manager_class.return_value = mock_file_manager

        mock_summary_storage = Mock()
        mock_summary_storage_class.return_value = mock_summary_storage

        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor

        # Create a Main instance without dependencies
        main = Main()

        # Verify that the dependencies were created and set correctly
        self.assertEqual(main.config, mock_config)
        self.assertEqual(main.transcriber, mock_transcriber)
        self.assertEqual(main.summarizer, mock_summarizer)
        self.assertEqual(main.file_manager, mock_file_manager)
        self.assertEqual(main.summary_storage, mock_summary_storage)
        self.assertEqual(main.processor, mock_processor)

        # Verify that the classes were called with the correct parameters
        mock_config_class.assert_called_once()
        mock_transcriber_class.assert_called_once_with(config=mock_config)
        mock_summarizer_class.assert_called_once_with(config=mock_config)
        mock_file_manager_class.assert_called_once_with(config=mock_config)
        mock_summary_storage_class.assert_called_once_with(config=mock_config)
        mock_processor_class.assert_called_once_with(
            transcriber=mock_transcriber,
            summarizer=mock_summarizer,
            file_manager=mock_file_manager,
            summary_storage=mock_summary_storage,
            config=mock_config,
        )

        # Verify that validate was called on the config
        mock_config.validate.assert_called_once()

    def test_run(self):
        """Test running the Main class."""
        # Configure the mocks
        test_files = ["file1.mp4", "file2.mp4"]
        self.mock_file_manager.get_files_to_process.return_value = test_files

        # Call the method under test
        self.main.run()

        # Verify that get_files_to_process was called with the correct parameters
        self.mock_file_manager.get_files_to_process.assert_called_once_with(
            self.mock_config.file_patterns
        )

        # Verify that process_file was called for each file
        self.assertEqual(self.mock_processor.process_file.call_count, len(test_files))
        for file_path in test_files:
            self.mock_processor.process_file.assert_any_call(file_path)

        # Verify that delete_zone_identifier_files was called
        self.mock_file_manager.delete_zone_identifier_files.assert_called_once()

    def test_run_with_no_files(self):
        """Test running the Main class when there are no files to process."""
        # Configure the mock to return an empty list
        self.mock_file_manager.get_files_to_process.return_value = []

        # Call the method under test
        self.main.run()

        # Verify that get_files_to_process was called
        self.mock_file_manager.get_files_to_process.assert_called_once()

        # Verify that process_file was not called
        self.mock_processor.process_file.assert_not_called()

        # Verify that delete_zone_identifier_files was still called
        self.mock_file_manager.delete_zone_identifier_files.assert_called_once()

    @patch("main.logger")
    @patch("main.os._exit")
    def test_main_entry_point(self, mock_exit, mock_logger):
        """Test the main entry point."""
        # Configure the mocks
        mock_main = Mock()

        # Patch the Main class to return our mock
        with patch("main.Main", return_value=mock_main):
            # Call the main entry point
            import main

            if hasattr(main, "__name__"):
                old_name = main.__name__
                main.__name__ = "__main__"
                try:
                    # This will execute the code in the if __name__ == '__main__' block
                    exec(open("main.py").read())
                finally:
                    main.__name__ = old_name

            # Verify that Main was instantiated and run was called
            mock_main.run.assert_called_once()

            # Verify that os._exit was called
            mock_exit.assert_called_once_with(0)

    @patch("main.logger")
    @patch("main.os._exit")
    def test_main_entry_point_with_exception(self, mock_exit, mock_logger):
        """Test the main entry point when an exception is raised."""
        # Configure the mocks
        mock_main = Mock()
        mock_main.run.side_effect = Exception("Test exception")

        # Patch the Main class to return our mock
        with patch("main.Main", return_value=mock_main):
            # Call the main entry point
            import main

            if hasattr(main, "__name__"):
                old_name = main.__name__
                main.__name__ = "__main__"
                try:
                    # This will execute the code in the if __name__ == '__main__' block
                    exec(open("main.py").read())
                finally:
                    main.__name__ = old_name

            # Verify that Main was instantiated and run was called
            mock_main.run.assert_called_once()

            # Verify that the error was logged
            mock_logger.error.assert_called_once_with("Error: Test exception")

            # Verify that os._exit was called
            mock_exit.assert_called_once_with(0)


if __name__ == "__main__":
    unittest.main()
