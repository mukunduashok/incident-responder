# Test Suite Documentation

## Test Structure

The test suite follows the **Test Pyramid** principle:

```
     /\
    /E2E\     <- Few E2E tests (slowest, most comprehensive)
   /------\
  /  Integ \   <- Some Integration tests (medium speed)
 /----------\
/    Unit    \ <- Many Unit tests (fastest, most focused)
--------------
```

### Directory Structure

```
tests/
├── unit/               # Unit tests (isolated, fast)
│   ├── test_constants.py
│   ├── test_config.py
│   ├── test_models.py
│   ├── test_log_utils.py
│   └── test_tools.py
├── integration/        # Integration tests (components working together)
│   ├── test_api.py
│   └── test_tools.py
├── e2e/               # End-to-end tests (full system)
│   └── test_investigation_flow.py
└── conftest.py        # Shared fixtures and configuration
```

## Running Tests

### All Tests
```bash
make test                 # Run all tests with coverage
pytest                    # Alternative: direct pytest
```

### By Test Type
```bash
make test-unit           # Run only unit tests (fast)
make test-integration    # Run only integration tests
make test-e2e            # Run only E2E tests (slow)
```

### With Coverage
```bash
make test-coverage       # Generate full coverage report
```

Coverage reports are generated in:
- Terminal: Immediate feedback
- HTML: `htmlcov/index.html` (detailed, browsable)
- XML: `coverage.xml` (for CI/CD tools)

### Watch Mode (Development)
```bash
make test-watch          # Re-run tests on file changes
```

### Specific Tests
```bash
pytest tests/unit/test_constants.py              # Single file
pytest tests/unit/test_constants.py::TestAPIConstants  # Single class
pytest tests/unit/test_constants.py::TestAPIConstants::test_api_title_is_string  # Single test
```

### Using Markers
```bash
pytest -m unit           # Run tests marked as @pytest.mark.unit
pytest -m integration    # Run integration tests
pytest -m "not slow"     # Skip slow tests
pytest -m slow           # Run only slow tests
```

## Test Coverage Goals

| Component | Target Coverage | Current Focus |
|-----------|----------------|---------------|
| Unit Tests | 80%+ | Individual functions and classes |
| Integration Tests | 70%+ | Multi-component interactions |
| E2E Tests | Key workflows | Critical user paths |

### Coverage by Module

- **Constants**: 100% (comprehensive validation)
- **Config**: 90%+ (environment handling)
- **Models**: 95%+ (validation logic)
- **Utils**: 85%+ (edge cases)
- **Tools**: 80%+ (file operations)
- **API Routes**: 75%+ (request/response flow)

## Test Categories

### Unit Tests (Fast, Isolated)
- Test single functions/classes in isolation
- Mock external dependencies
- No file I/O or network calls
- Should complete in milliseconds
- **Examples:**
  - `test_constants.py`: Validate constant values
  - `test_models.py`: Pydantic model validation
  - `test_log_utils.py`: Log parsing logic

### Integration Tests (Medium Speed)
- Test multiple components working together
- May use real files/databases
- Test API endpoints with all layers
- Should complete in seconds
- **Examples:**
  - `test_api.py`: Full API request/response flow
  - `test_tools.py`: Tools with actual files

### E2E Tests (Slow, Comprehensive)
- Test complete user workflows
- Full system integration
- Background task execution
- May take minutes to complete
- **Examples:**
  - `test_investigation_flow.py`: Complete investigation lifecycle

## Writing Tests

### Best Practices

1. **Follow AAA Pattern** (Arrange, Act, Assert)
```python
def test_example():
    # Arrange: Set up test data
    tool = LogParserTool()
    
    # Act: Execute the code
    result = tool._run(service_name="test", timestamp="2026-01-23")
    
    # Assert: Verify the outcome
    assert "Error" in result
```

2. **Use Descriptive Names**
```python
# Good
def test_parses_error_logs_with_database_timeout():
    pass

# Bad
def test_parser():
    pass
```

3. **Test One Thing Per Test**
```python
# Good
def test_validates_service_name():
    pass

def test_validates_alert_type():
    pass

# Bad  
def test_validation():  # Tests multiple things
    pass
```

4. **Use Fixtures for Reusable Data**
```python
@pytest.fixture
def sample_log_content():
    return "2026-01-23 ERROR [service] Error message"

def test_uses_fixture(sample_log_content):
    assert "ERROR" in sample_log_content
```

### Test Markers

Mark tests for selective execution:

```python
@pytest.mark.unit
def test_unit_example():
    pass

@pytest.mark.integration
def test_integration_example():
    pass

@pytest.mark.slow
@pytest.mark.e2e
def test_slow_e2e():
    pass
```

## Fixtures

Available in `conftest.py`:

- `temp_log_file`: Temporary log file with sample content
- `temp_report_dir`: Temporary directory for reports
- `sample_investigation_payload`: Standard API payload
- `sample_log_content`: Sample log entries
- `sample_report_content`: Sample report markdown
- `mock_git_commits`: Mock git commit data
- `reset_investigation_storage`: Auto-cleanup between tests

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example CI configuration
- name: Run Tests
  run: |
    pip install -e .[test]
    pytest --cov=src/incident_responder --cov-report=xml
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
```

## Debugging Tests

### Verbose Output
```bash
pytest -vv                    # Very verbose
pytest -vv -s                 # Show print statements
pytest --tb=long              # Full tracebacks
```

### Debug Single Test
```bash
pytest tests/unit/test_tools.py::TestLogParserTool::test_handles_missing_log_file -vv -s
```

### Drop into Debugger
```python
def test_example():
    import pdb; pdb.set_trace()  # Debugger breakpoint
    # ... test code
```

## Test Metrics

Current test metrics (updated automatically):

- **Total Tests**: ~60+ tests
- **Unit Tests**: ~40 tests (66%)
- **Integration Tests**: ~15 tests (25%)  
- **E2E Tests**: ~5 tests (9%)
- **Execution Time**:
  - Unit: <10 seconds
  - Integration: ~30 seconds
  - E2E: ~3 minutes (with timeout protections)

## Maintenance

### Adding New Tests

1. Determine test type (unit/integration/e2e)
2. Place in appropriate directory
3. Follow naming convention: `test_*.py`
4. Add appropriate markers
5. Update coverage targets if needed

### Updating Fixtures

Shared fixtures should:
- Be added to `conftest.py`
- Have clear docstrings
- Clean up resources (use `yield`)
- Be reusable across test types

## Coverage Reports

### Viewing Coverage

```bash
# Generate and open HTML report
make test-coverage
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Badges

Coverage percentage should be:
- ✅ Green: 80%+
- ⚠️ Yellow: 70-79%
- ❌ Red: <70%

## Troubleshooting

### Common Issues

1. **Tests failing locally but passing in CI**
   - Check environment variables
   - Verify file paths are absolute
   - Ensure clean state between tests

2. **Slow test execution**
   - Run unit tests only: `make test-unit`
   - Skip E2E tests: `pytest -m "not slow"`
   - Use `--lf` to run last failed tests first

3. **Import errors**
   - Ensure `src` is in PYTHONPATH (handled by conftest.py)
   - Check for circular imports
   - Verify package installation: `pip install -e .[test]`

## Contributing

When adding new features:
1. Write unit tests first (TDD)
2. Ensure >80% code coverage
3. Add integration tests for new endpoints
4. Update E2E tests for new workflows
5. Run full test suite before committing: `make test`
