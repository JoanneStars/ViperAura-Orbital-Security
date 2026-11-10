"""Evidence-backed checks strictly for the loopback ViperAura simulator.
These are configuration policy tests, NOT third-party CVE verification.
"""
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = 'http://127.0.0.1:8080'


def local_json(path, method='GET', payload=None, timeout=2):
    if not path.startswith('/') or '://' in path or '?' in path:
        raise ValueError('Only fixed, relative simulator routes are permitted.')
    body = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = Request(BASE + path, data=body, method=method,
                  headers={'Content-Type':'application/json'} if body else {})
    try:
        with urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read(65536))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read(65536))


def check_simulator():
    status, health = local_json('/health')
    if status != 200 or health.get('system') != 'ViperAura simulated ground station' or health.get('mode') != 'simulation':
        raise RuntimeError('Expected ViperAura loopback simulator not detected; checks cancelled.')
    _, policy = local_json('/security/status')
    diag_status, diag = local_json('/lab/diagnostics')
    results = []
    if diag_status == 200 and diag.get('lab_sensitive') is True and diag.get('training_only') is True:
        results.append({'id':'LAB-001','severity':'High','classification':'Confirmed lab policy violation',
            'title':'Anonymous access to restricted training diagnostics',
            'evidence':'GET /lab/diagnostics returned HTTP 200 with lab_sensitive=true and training_only=true.',
            'remediation':'Require authorization for sensitive diagnostic routes or remove them.'})
    elif diag_status == 403:
        results.append({'id':'LAB-001','severity':'Pass','classification':'Verified lab control',
            'title':'Training diagnostics deny anonymous access',
            'evidence':'GET /lab/diagnostics returned HTTP 403.',
            'remediation':'Retain restricted diagnostics access.'})
    else:
        results.append({'id':'LAB-001','severity':'Unknown','classification':'Inconclusive',
            'title':'Training diagnostics policy could not be verified',
            'evidence':f'GET /lab/diagnostics returned HTTP {diag_status}.',
            'remediation':'Inspect the simulator policy and handler.'})
    enabled = policy.get('auth_lockout_enabled')
    threshold = policy.get('max_failed_attempts')
    if enabled is False:
        sev, kind, detail = 'Medium','Confirmed lab policy violation','Simulator reports auth_lockout_enabled=false.'
    elif enabled is True and threshold == 3:
        sev, kind, detail = 'Pass','Verified configuration','Simulator reports lockout enabled after 3 failures (configuration claim only).'
    else:
        sev, kind, detail = 'Unknown','Inconclusive',f'Lockout policy reported: enabled={enabled}, threshold={threshold}.'
    results.append({'id':'LAB-002','severity':sev,'classification':kind,
        'title':'Authentication failure lockout configuration','evidence':detail,
        'remediation':'Enable and test an appropriate lockout or rate-limiting policy.'})
    return results


def test_authentication():
    """Use a synthetic identity and three failed requests to test enforced lockout."""
    from uuid import uuid4
    identity = 'probe-' + uuid4().hex[:12]
    statuses = []
    for _ in range(4):
        code, payload = local_json('/lab/authenticate', method='POST',
                                   payload={'identity':identity,'credential':'invalid-demo'})
        statuses.append((code, payload.get('result')))
    locked = statuses[-1] == (429,'blocked')
    return {'id':'LAB-003','severity':'Pass' if locked else 'High',
        'classification':'Verified lab control' if locked else 'Confirmed lab policy violation',
        'title':'Authentication lockout enforcement',
        'evidence':f'Synthetic login attempts HTTP statuses: {[s[0] for s in statuses]}; final result: {statuses[-1][1]}.',
        'remediation':'Keep lockout enforcement enabled for synthetic identities.' if locked else 'Enforce lockout after repeated failed authentication.'}


def fetch_telemetry_and_events():
    _, telemetry = local_json('/telemetry')
    _, events = local_json('/security/events')
    return telemetry, events.get('events',[])
