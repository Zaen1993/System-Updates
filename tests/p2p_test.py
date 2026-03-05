import unittest
import p2p_module

class TestP2PCommunication(unittest.TestCase):
    def setUp(self):
        self.node1 = p2p_module.P2PNode(port=6000)
        self.node2 = p2p_module.P2PNode(port=6001)
        self.node1.start()
        self.node2.start()

    def tearDown(self):
        self.node1.stop()
        self.node2.stop()

    def test_peer_connection(self):
        success = self.node1.connect_to_peer("127.0.0.1", 6001)
        self.assertTrue(success)

    def test_message_exchange(self):
        self.node1.connect_to_peer("127.0.0.1", 6001)
        test_message = "peer-to-peer-test-data"
        self.node1.send_message(test_message)
        received_message = self.node2.get_last_message()
        self.assertEqual(received_message, test_message)

if __name__ == '__main__':
    unittest.main()