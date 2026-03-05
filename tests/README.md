# System Testing Framework

This directory contains the testing suite for the system components. Proper testing ensures code quality, security, and functionality stability.

## Prerequisites
Install the required testing libraries:

```bash
pip install pytest pytest-cov pytest-asyncio pytest-mock
```

For Android client tests, ensure you have:

· Android SDK with API level 21+
· Emulator or physical device with developer options enabled

Test Structure

```
tests/
├── unit/                 # Unit tests for individual components
│   ├── test_crypto.py
│   ├── test_network.py
│   └── test_utils.py
├── integration/          # Integration tests for component interaction
│   ├── test_client_server.py
│   ├── test_database.py
│   └── test_api.py
├── performance/          # Performance and load tests
│   ├── test_load_balancer.py
│   └── test_concurrency.py
├── security/             # Security-focused tests
│   ├── test_encryption.py
│   └── test_authentication.py
├── android/              # Android client tests (instrumented)
│   ├── src/
│   └── build.gradle
└── fixtures/             # Test data and mocks
    ├── sample_commands.json
    └── test_keys/
```

Running Tests

Unit Tests

Run all unit tests:

```bash
pytest tests/unit/ -v
```

Run specific unit test file:

```bash
pytest tests/unit/test_crypto.py -v
```

Integration Tests

Start required services (database, Redis) before running integration tests:

```bash
docker-compose up -d postgres redis
pytest tests/integration/ -v --cov=server
```

Performance Tests

Run load tests with customizable parameters:

```bash
pytest tests/performance/test_load_balancer.py --users=100 --spawn-rate=10 -v
```

Security Tests

Run security-focused test suite:

```bash
pytest tests/security/ -v --tb=short
```

Android Client Tests

Run instrumented tests on connected device/emulator:

```bash
cd tests/android
./gradlew connectedAndroidTest
```

Test Coverage

Generate coverage report:

```bash
pytest --cov=server tests/ --cov-report=html --cov-report=term
```

Coverage reports will be generated in htmlcov/ directory.

Writing New Tests

Guidelines

1. Place unit tests in appropriate subdirectory
2. Name test files with test_ prefix
3. Use descriptive test names
4. Include both positive and negative test cases
5. Mock external dependencies
6. Clean up resources after tests

Example Unit Test

```python
import pytest
from server.core.crypto_manager import CryptoManager

def test_encryption_decryption():
    """Test that data can be encrypted and decrypted successfully."""
    crypto = CryptoManager()
    test_data = b"sensitive information"
    key = crypto.generate_key()
    
    encrypted = crypto.encrypt(test_data, key)
    decrypted = crypto.decrypt(encrypted, key)
    
    assert decrypted == test_data
```

Example Integration Test

```python
import pytest
import asyncio
from server.communication.network_handler import NetworkHandler

@pytest.mark.asyncio
async def test_device_registration():
    """Test device registration flow."""
    handler = NetworkHandler()
    device_id = "test_device_001"
    
    result = await handler.register_device(device_id)
    assert result["status"] == "success"
    assert result["device_id"] == device_id
```

Continuous Integration

The test suite runs automatically on GitHub Actions for every push and pull request. Configuration is in .github/workflows/test.yml.

CI Pipeline Stages

1. Lint code (flake8, pylint)
2. Run unit tests
3. Run integration tests
4. Generate coverage report
5. Build Android client (smoke test)

Troubleshooting Common Test Failures

Issue Possible Cause Solution
Database connection errors PostgreSQL not running docker-compose up -d postgres
Port conflicts Services already running Stop conflicting services or change ports
Android tests fail Device not authorized Check adb devices and authorize device
Async test timeouts Missing event loop Add @pytest.mark.asyncio decorator

Test Data

Sample test data is located in fixtures/:

· sample_commands.json: Example command payloads
· test_keys/: Test encryption keys (do not use in production)

Security Notes

· Never use real credentials in tests
· Test keys are for development only
· All test data is encrypted before storage
· Network tests use isolated environments

Contributing

When adding new features:

1. Write tests before implementing the feature (TDD approach)
2. Ensure coverage remains above 80%
3. Update this documentation if test structure changes
4. Run full test suite locally before submitting PR

License

Proprietary — All rights reserved. This testing framework is part of the internal development process.