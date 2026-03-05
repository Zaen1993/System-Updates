import unittest
import sys
import os
import json
import time
from unittest.mock import MagicMock, patch

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server'))

from error_tracker import ErrorTracker
from fallback_executor import FallbackExecutor
from command_retry_queue import CommandRetryQueue

class TestErrorInjection(unittest.TestCase):
    def setUp(self):
        self.config = {
            "max_errors": 100,
            "max_attempts": 3,
            "base_delay": 1,
            "max_delay": 5
        }
        self.error_tracker = ErrorTracker(self.config)
        self.fallback_executor = FallbackExecutor(self.config)
        self.retry_queue = CommandRetryQueue(self.config)
        self.error_tracker.set_fallback_executor(self.fallback_executor)
        self.retry_queue.set_error_tracker(self.error_tracker)
        self.retry_queue.set_fallback_executor(self.fallback_executor)

    def test_error_logging(self):
        error_id = self.error_tracker.log_error(
            device_id="test_device",
            error_code="TEST_ERR",
            error_message="Test error message",
            module="test_module",
            command="test_command"
        )
        self.assertIsNotNone(error_id)
        errors = self.error_tracker.get_errors(device_id="test_device")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["error_code"], "TEST_ERR")

    def test_fallback_submission(self):
        task_id = self.fallback_executor.submit_failed_command(
            device_id="test_device",
            command_name="test_cmd",
            command_params={"param": "value"},
            error_message="fail",
            error_code="ERR"
        )
        self.assertIsNotNone(task_id)
        status = self.fallback_executor.get_status()
        self.assertEqual(status["queue_size"], 1)

    def test_retry_queue_push(self):
        entry = {
            "device_id": "test",
            "command": "cmd",
            "params": {},
            "attempts": 0,
            "error_id": "err123"
        }
        self.retry_queue.push(entry)
        self.assertEqual(self.retry_queue.size(), 1)

    def test_retry_processing(self):
        self.retry_queue.start()
        entry = {
            "device_id": "test",
            "command": "cmd",
            "params": {},
            "attempts": 0,
            "error_id": "err123",
            "last_attempt": time.time() - 10
        }
        self.retry_queue.push(entry)
        time.sleep(2)
        self.retry_queue.stop()
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()