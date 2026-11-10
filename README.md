# ViperAura Orbital Security — Orbital + Ground Station Digital Twin

An educational aerospace cybersecurity lab combining an **offline geographic Earth globe**, **multiple predicted orbits from public TLE data**, a **loopback-only mock satellite ground station**, an explicitly authorized Nmap service inventory, SQLite scan history, and PDF reporting.

## Windows / VS Code — first-time setup

1. Extract the entire ZIP. In VS Code, choose **File → Open Folder**, then select the inner `ViperAura-Orbital-Security` folder containing `app.py`, `orbit.py`, `ground_station.py`, `earth_land_mask.npz` and `requirements.txt`.
2. Open **Terminal → New Terminal**. Do **not** use VS Code's *Run Python File* button for `app.py`.
3. In PowerShell, type these commands one at a time:

```powershell
python3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

If `python3` is unavailable, replace `python3` with `python`. Keep the terminal open; Streamlit should show a local URL, typically `http://localhost:8501`.

**Terminal 2: Ground station simulator**

From the same project folder, open another terminal and run:

```powershell
.\.venv\Scripts\python.exe ground_station.py
```

Then visit `http://127.0.0.1:8080/telemetry`. The mock service provides synthetic telemetry and does not accept spacecraft commands. End it with `Ctrl+C`.

## Walkthrough

- **Orbital tracking**: View two simulated orbits immediately. To load real predicted orbits, paste up to five *actual* public TLE records into the same text area. Each record contains optional name + exact TLE lines `1 ...` and `2 ...` — sample placeholder text is *not* valid.
- **Ground station twin**: See architecture and status of the local telemetry simulator.
- **Lab scanner**: Install [Nmap](https://nmap.org/download.html), ensure `nmap` is in PATH, check the authorization confirmation, target `127.0.0.1`, and run a scan while `ground_station.py` is running. The program only scans a small fixed TCP port list, including `8080`; if the service is detected, it appears in the findings. TCP port exposure is not proof of a vulnerability.
- **Scan history**: Review local SQLite records and download a PDF report from the scanner tab.

## Scope and limitations

- The realistic globe is colored using bundled low-resolution geographic land mask data; it works offline without extra mapping services. It is an illustrative geographic Earth: its longitude rotation is **not synchronized to the inertial orbit reference frame**. Do not interpret the marker as ground coordinates.
- The TLE path is a Skyfield/SGP4 **prediction**, not a direct spacecraft connection or a live RF data feed. Accuracy depends on TLE age.
- There is **no actual communications link** to an ISS, Hubble, NASA, SpaceX, or other ground station. Dashed communications edges in the digital twin are purely illustrative.
- The simulator binds only to `127.0.0.1:8080` and exposes synthetic `/health` and `/telemetry` read-only JSON endpoints. No uplink, real telemetry, or control features are included.
- Nmap is only permitted on lab-owned or explicitly authorized hosts. The scanner restricts inputs to up to 16 private or loopback IPv4 addresses and selected TCP ports.
- Security findings are *unverified configuration review suggestions*. No exploit execution or authenticated CVE verification is performed.

## Test

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The dark navy and purple theme lives in `app.py` and `.streamlit/config.toml`. You can copy this updated folder into your existing CSC workspace, but avoid overwriting any `viperaura.db` file containing your prior scan history.

## Version 3 — Synthetic telemetry, authentication monitoring, and evidence checks

The **Telemetry & security** tab now displays temperature, battery, solar-power output and signal quality from the loopback simulator. It also displays synthetic authentication activity, an optional authentication lockout test, evidence-based lab configuration checks, a PDF evidence export and SQLite audit history. The satellite imagery and public orbital predictions are separate from this local-only telemetry simulation.

### 1. Run in secure mode (default)

Open the project folder in VS Code. Run the dashboard in Terminal 1:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

If dependencies are not installed in the project environment, first run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

In Terminal 2, run the ground station:

```powershell
.\.venv\Scripts\python.exe ground_station.py
```

Visit **Telemetry & security**, click **Audit simulator configuration**, then **Test synthetic login lockout**. Secure mode should show passing lab controls; after the lockout test, the authentication log should show three denied attempts followed by one blocked attempt. The tester uses generated synthetic identities; it does not attempt to log in to any real system.

### 2. Run the deliberately misconfigured training scenario

Stop Terminal 2 with `Ctrl+C`. In Terminal 2, start the *same localhost-only* simulator in training mode:

```powershell
$env:VIPERAURA_LAB_MODE="misconfigured"
.\.venv\Scripts\python.exe ground_station.py
```

Return to the Streamlit dashboard. Click **Audit simulator configuration**, then **Test synthetic login lockout**. The lab deliberately exposes a simulated restricted diagnostics route and disables synthetic lockout. The checks should produce confirmed **lab policy violations** (not real satellite vulnerabilities). Check the exact observed HTTP statuses in the **evidence** column, export the PDF and review the history tab. To return to secure mode, stop the simulator and run:

```powershell
Remove-Item Env:VIPERAURA_LAB_MODE
.\.venv\Scripts\python.exe ground_station.py
```

**Important:** The simulator binds ONLY to `127.0.0.1:8080`, has no satellite command interface and never accesses NASA, ISS, SpaceX or any other real spacecraft or ground-system endpoint. The `DEMO-ONLY` training credential is not a real secret or real access grant. It is never stored in the authentication events. The authentication simulation resets when you restart the simulator. Assessment history in `viperaura.db` persists across restarts.

### Evidence semantics

- `LAB-001`: **Verified against simulator policy** using the response from `/lab/diagnostics`: access denied `403` versus deliberately exposed `200` with a synthetic sensitive-data marker.
- `LAB-002`: **Observed simulator configuration claim**, from `/security/status`; not proof of behavior.
- `LAB-003`: **Tested enforcement** using four harmless synthetic login attempts, verifying whether attempt 4 is blocked with `429`.
- The Nmap scanner still reports **open-port observations and unverified configuration-review guidance**. This upgrade does not claim to authenticate any published CVEs, perform OpenVAS scans, or verify vulnerabilities in any real system.

### Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The full test suite covers orbital calculations/figures, network scope restrictions, PDF output, the simulator's secure and intentionally misconfigured modes, and simulated authentication lockout.
