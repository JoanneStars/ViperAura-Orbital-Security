import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
DB = Path(__file__).with_name('viperaura.db')

def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS scans (id INTEGER PRIMARY KEY, timestamp TEXT NOT NULL, target TEXT NOT NULL, findings TEXT NOT NULL)')
        conn.execute('CREATE TABLE IF NOT EXISTS security_audits (id INTEGER PRIMARY KEY, timestamp TEXT NOT NULL, findings TEXT NOT NULL)')

def save_scan(target, rows):
    with sqlite3.connect(DB) as conn:
        conn.execute('INSERT INTO scans (timestamp,target,findings) VALUES (?,?,?)',(datetime.now(timezone.utc).isoformat(),target,json.dumps(rows)))

def history():
    with sqlite3.connect(DB) as conn:
        return conn.execute('SELECT id,timestamp,target,findings FROM scans ORDER BY id DESC LIMIT 50').fetchall()


def save_audit(findings):
    with sqlite3.connect(DB) as conn:
        conn.execute('INSERT INTO security_audits (timestamp,findings) VALUES (?,?)',
                     (datetime.now(timezone.utc).isoformat(), json.dumps(findings)))

def audit_history():
    with sqlite3.connect(DB) as conn:
        return conn.execute('SELECT id,timestamp,findings FROM security_audits ORDER BY id DESC LIMIT 50').fetchall()
