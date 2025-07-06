# Copilot Instructions for YouTube Transcript Summarizer

This document provides guidelines and best practices for using GitHub Copilot and Copilot Chat in the YouTube Transcript Summarizer project. It is based on the project's testing strategy and codebase structure.

## General Guidelines

- **Write clear, modular code**: Break down functionality into small, testable components.
- **Follow the testing strategy**: Ensure all new code is covered by unit and integration tests.
- **Use mocking**: Isolate external dependencies (e.g., OpenAI, Google Gemini, Notion) in tests using mocks.
- **Naming conventions**: Use descriptive names for files, classes, methods, and variables. Test files should be named `test_*.py`.
- **Documentation**: Add docstrings and comments to explain complex logic and test cases.

## Testing Requirements

- All new features must include corresponding tests.
- Use `unittest` and `unittest.mock` for writing and structuring tests.
- Test edge cases and error conditions, not just the happy path.
- Use `setUp` and `tearDown` methods for test fixtures.
- Ensure tests are isolated and do not depend on external services.

## Test Coverage Expectations

- **FileManager**: Filename sanitization, file saving/deletion, file listing.
- **Transcriber**: Initialization, transcription methods, error handling.
- **Summarizer**: Initialization, prompt templates, summarization with all supported models, error handling.
- **YouTubeDownloader**: Downloading with different tools, error handling.
- **SummaryStorage**: Chunking, saving summaries (with/without Notion), error handling.
- **Config**: Initialization, environment variable handling, validation.
- **Processor**: Title extraction, processing flow, error handling.
- **Main**: Dependency injection, main entry point, error handling.

## Running Tests

- To run all tests: `python -m unittest discover`
- To run a specific test: `python -m unittest test_file_name.py`

## Example Test Structure

```python
import unittest
from unittest.mock import Mock
from my_component import MyComponent

class TestMyComponent(unittest.TestCase):
    def setUp(self):
        self.mock_dependency = Mock()
        self.component = MyComponent(dependency=self.mock_dependency)

    def test_my_method(self):
        self.mock_dependency.some_method.return_value = "expected_result"
        result = self.component.my_method()
        self.assertEqual(result, "expected_result")
        self.mock_dependency.some_method.assert_called_once()
```

## Best Practices

- Isolate components in tests using mocks
- Aim for high test coverage
- Write readable, well-documented tests
- Test edge cases and error conditions
- Use specific assertions
- Document tests with docstrings and comments

---

_This file is auto-generated to help Copilot and contributors follow project conventions and maintain high code quality._
