import threading
import unittest
from urllib.error import URLError
from ground_station import create_server, LabState
from security_checks import check_simulator, test_authentication, fetch_telemetry_and_events
from report import make_security_pdf


class TestSecurityTwin(unittest.TestCase):
    def test_state_lockout(self):
        s=LabState()
        for _ in range(3):
            self.assertEqual(s.attempt('test','wrong'),'denied')
        self.assertEqual(s.attempt('test','wrong'),'blocked')
        self.assertEqual(len(s.recent_events()),4)
        self.assertFalse(any('wrong' in repr(e) for e in s.recent_events()))

    def test_misconfigured_mode(self):
        s=LabState(misconfigured=True)
        for _ in range(4): self.assertEqual(s.attempt('test','wrong'),'denied')

    def test_pdf(self):
        rows=[{'id':'LAB-001','title':'Example','severity':'High','classification':'Confirmed lab policy violation','evidence':'HTTP 200','remediation':'Restrict endpoint'}]
        self.assertTrue(make_security_pdf(rows).startswith(b'%PDF'))

    def test_end_to_end_secure_mode(self):
        from unittest.mock import patch
        server=create_server(port=0,misconfigured=False)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            # Adapt fixed loopback base in tests to dynamic port; no remote endpoint.
            with patch('security_checks.BASE', f'http://127.0.0.1:{server.server_port}'):
                result=check_simulator()
                self.assertEqual([x['severity'] for x in result],['Pass','Pass'])
                auth=test_authentication()
                self.assertEqual(auth['severity'],'Pass')
                telemetry,events=fetch_telemetry_and_events()
                self.assertEqual(telemetry['source'],'synthetic')
                self.assertEqual(len(events),5)
        finally:
            server.shutdown();server.server_close();thread.join(timeout=3)

    def test_end_to_end_misconfigured_mode(self):
        from unittest.mock import patch
        server=create_server(port=0,misconfigured=True)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            with patch('security_checks.BASE',f'http://127.0.0.1:{server.server_port}'):
                result=check_simulator()
                self.assertEqual([x['severity'] for x in result],['High','Medium'])
                self.assertEqual(test_authentication()['severity'],'High')
        finally:
            server.shutdown();server.server_close();thread.join(timeout=3)

if __name__ == '__main__': unittest.main()
