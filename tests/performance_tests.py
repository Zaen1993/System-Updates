import os
import unittest
import requests
import time
import threading

class TestSystemPerformance(unittest.TestCase):
    def setUp(self):
        self.load_balancer_url = os.environ.get('LOAD_BALANCER_URL', 'http://localhost:80')
        self.num_clients = int(os.environ.get('PERF_TEST_CLIENTS', 100))
        self.timeout = float(os.environ.get('PERF_TEST_TIMEOUT', 5.0))

    def simulate_client(self, client_id):
        payload = {"device_id": f"perf_test_{client_id}", "payload": "test_data"}
        try:
            requests.post(f"{self.load_balancer_url}/api/v1/collect", json=payload, timeout=2)
        except requests.exceptions.RequestException:
            pass

    def test_high_load_handling(self):
        threads = []
        start_time = time.time()
        for i in range(self.num_clients):
            t = threading.Thread(target=self.simulate_client, args=(i,))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        end_time = time.time()
        duration = end_time - start_time
        print(f"\nProcessed {self.num_clients} requests in {duration:.2f} seconds.")
        self.assertLess(duration, self.timeout, f"System too slow: {duration:.2f}s > {self.timeout}s")

if __name__ == '__main__':
    unittest.main()