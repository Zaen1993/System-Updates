# Tests Directory

This directory contains test scripts for the System Updates project.

## Structure

- `integration_tests.py` – End-to-end integration tests.
- `unit_tests.py` – Unit tests for core modules.
- `performance_tests.py` – Performance benchmarks.
- `lidar_test.py` – Tests for LiDAR scanner (placeholder).
- `p2p_test.py` – Tests for P2P networking.

## Running Tests

To run all tests:

```bash
python -m unittest discover tests
```

To run a specific test:

```bash
python -m unittest tests.test_module
```

Requirements

Install test dependencies:

```bash
pip install -r server/requirements.txt
```

Notes

· Some tests may require a running server or device.
· Mock objects are used where external dependencies are unavailable.

```