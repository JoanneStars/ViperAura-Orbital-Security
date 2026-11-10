"""Local-only digital twin with synthetic telemetry and training-only authentication.
No RF, remote connections, or spacecraft commands. Demo credentials have no privileges.
"""
import json
import os
import threading
from collections import deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST, PORT = '127.0.0.1', 8080
MAX_BODY = 2048


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class LabState:
    def __init__(self, misconfigured=False):
        self.misconfigured = misconfigured
        self.events = deque(maxlen=150)
        self.failures = {}
        self.lock = threading.Lock()

    def record(self, event, identity='system', result='info'):
        with self.lock:
            entry = {'timestamp_utc': utc_now(), 'event': event, 'identity': identity, 'result': result}
            self.events.append(entry)
            return entry

    def attempt(self, identity, credential):
        # A fixed simulation-only example, never a real session or control grant.
        identity = identity[:40]
        with self.lock:
            count = self.failures.get(identity, 0)
            if count >= 3 and not self.misconfigured:
                result, event = 'blocked', 'authentication_locked'
            elif identity == 'lab-operator' and credential == 'DEMO-ONLY':
                result, event = 'accepted_simulation', 'authentication_simulated'
                self.failures[identity] = 0
            else:
                result, event = 'denied', 'authentication_failed'
                self.failures[identity] = count + 1
            self.events.append({'timestamp_utc':utc_now(), 'event':event,'identity':identity,'result':result})
        return result

    def recent_events(self):
        with self.lock:
            return list(reversed(self.events))


def make_handler(state):
    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, payload):
            raw = json.dumps(payload).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Length',str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            if self.path == '/health':
                self.respond(200, {'system':'ViperAura simulated ground station','status':'nominal',
                                    'mode':'simulation','time_utc':utc_now()})
            elif self.path == '/telemetry':
                self.respond(200, {'source':'synthetic','timestamp_utc':utc_now(), 'spacecraft':'SIM-LEO-01',
                    'battery_percent':87.4, 'solar_array_watts':212.8, 'temperature_c':21.3,
                    'signal_quality_db':17.2, 'altitude_km':420.0, 'link_state':'simulated',
                    'command_uplink_enabled':False})
            elif self.path == '/security/status':
                self.respond(200, {'mode':'simulation', 'auth_lockout_enabled':not state.misconfigured,
                    'max_failed_attempts':3 if not state.misconfigured else None,
                    'diagnostics_auth_required':not state.misconfigured,
                    'policy':'Diagnostics must not be anonymously accessible; lockout required after 3 failures.'})
            elif self.path == '/security/events':
                self.respond(200, {'source':'synthetic', 'events':state.recent_events()})
            elif self.path == '/lab/diagnostics':
                if state.misconfigured:
                    state.record('diagnostics_access',result='exposed')
                    self.respond(200, {'lab_sensitive':True, 'training_only':True,
                        'note':'Synthetic diagnostics exposed anonymously in misconfiguration mode.'})
                else:
                    state.record('diagnostics_access',result='blocked')
                    self.respond(403, {'error':'Authentication required. This simulation has no privileged login.'})
            else:
                self.respond(404,{'error':'Unknown simulator route'})

        def do_POST(self):
            if self.path != '/lab/authenticate':
                self.respond(404,{'error':'Unknown simulator route'}); return
            try:
                length = int(self.headers.get('Content-Length','0'))
                if length < 1 or length > MAX_BODY:
                    self.respond(413,{'error':'Invalid request size'}); return
                data = json.loads(self.rfile.read(length))
                identity = str(data.get('identity',''))
                credential = str(data.get('credential',''))
                if not 1 <= len(identity) <= 40 or len(credential) > 80:
                    self.respond(400,{'error':'Invalid lab identity'}); return
            except (ValueError, TypeError, json.JSONDecodeError):
                self.respond(400,{'error':'Invalid JSON'}); return
            outcome = state.attempt(identity,credential)
            code = 200 if outcome == 'accepted_simulation' else 429 if outcome == 'blocked' else 401
            self.respond(code,{'result':outcome,'simulation_only':True,'real_access_granted':False})

        def log_message(self, fmt, *args):
            pass
    return Handler


def create_server(port=PORT, misconfigured=False):
    state = LabState(misconfigured=misconfigured)
    return ThreadingHTTPServer((HOST,port),make_handler(state))


if __name__ == '__main__':
    misconfigured = os.getenv('VIPERAURA_LAB_MODE','secure').strip().lower() == 'misconfigured'
    server = create_server(misconfigured=misconfigured)
    print(f'ViperAura ground-station lab: http://{HOST}:{PORT} ({"MISCONFIGURED TRAINING" if misconfigured else "SECURE"} mode)')
    print('Synthetic local-only endpoints; Ctrl+C to stop.')
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
