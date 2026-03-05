import unittest
from unittest.mock import MagicMock
import lidar_module

class TestLidarModule(unittest.TestCase):
    def setUp(self):
        self.lidar = lidar_module.LidarScanner(port='/dev/ttyUSB0')

    def test_scan_functionality(self):
        self.lidar.read_data = MagicMock(return_value=[1.2, 1.5, 0.9])
        data = self.lidar.perform_scan()
        self.assertEqual(len(data), 3)
        self.assertIsInstance(data, list)

    def test_connection_error(self):
        self.lidar.connect = MagicMock(side_effect=Exception("Connection Failed"))
        with self.assertRaises(Exception):
            self.lidar.perform_scan()

if __name__ == '__main__':
    unittest.main()