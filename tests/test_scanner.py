import unittest
from scanner import validate_target, assess
class TestScanner(unittest.TestCase):
    def test_loopback(self): self.assertEqual(validate_target('127.0.0.1'),'127.0.0.1/32')
    def test_private(self): self.assertEqual(validate_target('192.168.56.10'),'192.168.56.10/32')
    def test_public_blocked(self):
        with self.assertRaises(ValueError): validate_target('8.8.8.8')
    def test_large_range_blocked(self):
        with self.assertRaises(ValueError): validate_target('192.168.0.0/24')
    def test_telnet(self): self.assertEqual(assess(23,'telnet')[0],'High')
if __name__=='__main__': unittest.main()
