## 🚨 Never Upload Secrets

- Do not store API keys or `.env` in repo.
- Use `.env.example` with placeholders.
- If a secret is leaked: rotate credentials, purge history, notify team.

## 🐍 Python Code Standards

### General Principles
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write descriptive docstrings for classes and methods
- Prefer composition over inheritance
- Use dependency injection for better testability

### Error Handling
- Use specific exception types
- Log errors with appropriate detail levels
- Implement graceful degradation (OpenAI → Gemini → Ollama)
- Always clean up resources in finally blocks

### Testing Requirements
- Write unit tests for all new functionality
- Use unittest.mock for external dependencies
- Maintain test coverage above 90%
- Test both success and error scenarios
- Include integration tests for workflow validation

### File Organization
- Keep modules focused and single-purpose
- Use interfaces (`*_interface.py`) for abstract contracts
- Place tests in files with `test_` prefix
- Group related functionality in appropriate modules

## 🔧 Architecture Rules

### Dependency Management
- Use dependency injection in constructors
- Make external dependencies optional with sensible defaults
- Avoid tight coupling between modules
- Use configuration objects for shared settings

### API Integration
- Always handle API rate limits and errors
- Implement retry logic with exponential backoff
- Use environment variables for API keys
- Support multiple LLM providers with fallback

### File Handling
- Sanitize all user-provided filenames
- Use absolute paths for clarity
- Clean up temporary files after processing
- Validate file formats before processing

## 📦 Docker & Deployment

- Use official Python base images
- Pin specific versions for reproducibility
- Minimize image layers and size
- Include health checks for services
- Use multi-stage builds when appropriate

## 🧪 Testing Philosophy

- Test behavior, not implementation
- Mock external services completely
- Use descriptive test method names
- Group tests by functionality
- Maintain test isolation and independence
