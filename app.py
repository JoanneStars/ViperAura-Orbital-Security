import pandas as pd
import streamlit as st
from orbit import demo_positions, from_tle, multi_orbital_figure, parse_multiple_tles
from topology import topology_figure, simulator_health
from scanner import scan, validate_target
from storage import init_db, save_scan, history, save_audit, audit_history
from report import make_pdf, make_security_pdf
from security_checks import check_simulator, test_authentication, fetch_telemetry_and_events

st.set_page_config(page_title='ViperAura Orbital Security',page_icon='🛰️',layout='wide')
st.markdown("""
<style>
/* ViperAura Orbital Security | Midnight Orbit theme */
.stApp {
  background: radial-gradient(ellipse at 76% 5%, #1b2450 0%, #0c1530 35%, #070e20 78%);
  color: #ecf2ff;
}
[data-testid="stHeader"] { background: transparent; }
h1, h2, h3, [data-testid="stMarkdownContainer"] p { color: #eaf1ff; }
[data-testid="stCaptionContainer"], .stCaption { color: #aebcde !important; }
/* Crucial fix: all input fields, including the pasted TLE text box */
.stTextArea textarea,
.stTextInput input {
  background-color: #111e3b !important;
  color: #f2f6ff !important;
  border: 1px solid #435b8a !important;
  border-radius: 12px !important;
  caret-color: #b896ff !important;
  -webkit-text-fill-color: #f2f6ff !important;
}
.stTextArea textarea::placeholder,
.stTextInput input::placeholder {
  color: #91a3c9 !important;
  -webkit-text-fill-color: #91a3c9 !important;
  opacity: 1;
}
.stTextArea textarea:focus, .stTextInput input:focus {
  border-color: #ad8cff !important;
  box-shadow: 0 0 0 1px #ad8cff, 0 0 18px #ad8cff30 !important;
}
/* Maintain dark backgrounds for widget wrappers across Streamlit releases */
[data-baseweb="textarea"], [data-baseweb="input"] {
  background-color: #111e3b !important;
  border-radius: 12px !important;
}
[data-testid="stMetric"] {
  background: #142343;
  border: 1px solid #2f416c;
  padding: 16px;
  border-radius: 14px;
}
.stTabs [data-baseweb="tab-list"] { gap: 14px; }
.stTabs [data-baseweb="tab"] { color: #b9c8e8; }
.stTabs [aria-selected="true"] { color: #d5baff !important; }
.stTabs [data-baseweb="tab-highlight"] { background-color: #b78aff; }
.stButton button[kind="primary"] {
  background: linear-gradient(100deg, #6847c8, #865ae8);
  color: white;
  border: 1px solid #aa8afa;
}
.stButton button[kind="primary"]:hover { background: #9672ef; }
/* Notification banners, including the green TLE-success banner */
[data-testid="stAlert"] { border-radius: 12px; }
[data-testid="stDataFrame"] { border: 1px solid #2f416c; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)
init_db()
st.title('🛰️ ViperAura Orbital Security')
st.caption('Satellite orbital visualization + explicitly authorized ground-network lab assessment')
orbital_tab, station_tab, monitoring_tab, security_tab, history_tab = st.tabs(['🌍 Orbital tracking','📡 Ground station twin','📈 Telemetry & security','🛡️ Lab scanner','📚 Scan history'])
with orbital_tab:
    st.subheader('3D Satellite Visualization · Earth & Multiple Orbits')
    st.caption('Offline geographic Earth globe with coastline detail. Earth orientation is illustrative; TLE orbit predictions are inertial trajectories, not ground tracks.')
    mode=st.radio('Orbital data', ['Demonstration orbits (simulated)','Paste public TLE data'],horizontal=True)
    orbits=[]
    if mode.startswith('Demonstration'):
        orbits=[(demo_positions(),'Demo LEO 01'),(demo_positions(altitude_km=800,inclination=97.4,phase=1.3),'Demo LEO 02')]
        st.info('These two orbits are simulations, not real spacecraft telemetry.')
    else:
        st.caption('Paste up to five public satellite TLE records, one after another. Each record is a satellite name (optional), line 1 and line 2.')
        tle=st.text_area('Two-line element data (TLE)',height=170,
            placeholder='ISS (ZARYA)\n1 [paste complete actual TLE line]\n2 [paste complete actual TLE line]\n\nHUBBLE SPACE TELESCOPE\n1 [paste complete actual TLE line]\n2 [paste complete actual TLE line]')
        if tle.strip():
            try:
                for group in parse_multiple_tles(tle):
                    xyz,name,age=from_tle(group)
                    orbits.append((xyz,name))
                    st.success(f'Loaded {name} · TLE epoch age {age:.1f} days')
                    if age > 14: st.warning(f'{name}: orbital data may be stale; use a newer TLE.')
            except Exception as exc:
                st.error(str(exc))
                orbits=[]
        else:
            st.info('Paste actual current orbital elements from CelesTrak. A demo orbit is shown until then.')
        if not orbits: orbits=[(demo_positions(),'Demonstration satellite')]
    st.plotly_chart(multi_orbital_figure(orbits),use_container_width=True)
    st.caption('Public TLEs are only used for trajectory predictions. This is not an RF receiver, satellite connection, or live tracking feed.')

with station_tab:
    st.subheader('Ground Station Digital Twin')
    st.caption('A harmless local telemetry simulation, visually associated with the orbit view; no actual satellite is contacted.')
    online=simulator_health()
    if online: st.success('Local ground station detected at 127.0.0.1:8080')
    else: st.info('Simulator is offline. Open a separate VS Code terminal and run: python3 ground_station.py (or python ground_station.py).')
    st.plotly_chart(topology_figure(online,st.session_state.get('last_rows',[])),use_container_width=True)
    st.markdown('**Test endpoints (only available while simulator is running)**')
    st.code('http://127.0.0.1:8080/health\nhttp://127.0.0.1:8080/telemetry',language='text')
    if online:
        from urllib.request import urlopen
        import json
        try:
            with urlopen('http://127.0.0.1:8080/telemetry',timeout=1.5) as response:
                telemetry=json.loads(response.read(2048))
            st.json(telemetry)
        except Exception as exc: st.warning('Telemetry endpoint is temporarily unavailable.')
    st.caption('Purple dotted link is illustrative only. No RF signal, command transmission, or direct network connection exists between the ISS and this simulator.')


with monitoring_tab:
    st.subheader('Synthetic Spacecraft Telemetry & Authentication Monitoring')
    st.caption('All data and identities are simulated locally. Nothing is received from or transmitted to an actual satellite.')
    online = simulator_health()
    if not online:
        st.info(r'Start the loopback ground station in Terminal 2: .\.venv\Scripts\python.exe ground_station.py')
    else:
        if st.button('Refresh telemetry and authentication events'):
            st.rerun()
        try:
            snapshot, events = fetch_telemetry_and_events()
            a,b,c,d = st.columns(4)
            a.metric('Battery',f"{snapshot['battery_percent']:.1f}%")
            b.metric('Solar power',f"{snapshot['solar_array_watts']:.1f} W")
            c.metric('Temperature',f"{snapshot['temperature_c']:.1f} °C")
            d.metric('Signal quality',f"{snapshot['signal_quality_db']:.1f} dB")
            st.caption(f"Telemetry source: {snapshot.get('source')} | Generated UTC: {snapshot.get('timestamp_utc')} | Uplink disabled: {not snapshot.get('command_uplink_enabled')}")
            st.markdown('**Synthetic authentication log**')
            if events:
                st.dataframe(pd.DataFrame(events),hide_index=True,use_container_width=True)
                denied=sum(e.get('event')=='authentication_failed' for e in events)
                blocked=sum(e.get('event')=='authentication_locked' for e in events)
                if denied>=3: st.warning(f'Authentication monitoring: {denied} failed synthetic attempts, {blocked} blocked.')
            else:
                st.info('No authentication events yet. Run the optional lockout test below to generate safe synthetic events.')
        except Exception as exc:
            st.error(f'Local telemetry not available: {exc}')
        st.divider()
        st.subheader('Evidence-based Lab Security Checks')
        st.caption('Security checks inspect ONLY the known local simulator. Results report specific observed HTTP responses and configuration claims—not CVE verification.')
        c1,c2=st.columns(2)
        with c1:
            run_check=st.button('Audit simulator configuration',type='primary')
        with c2:
            run_auth=st.button('Test synthetic login lockout')
        if run_check or run_auth:
            try:
                if run_check:
                    findings=check_simulator()
                else:
                    findings=st.session_state.get('audit_findings',[])
                    findings=[f for f in findings if f['id']!='LAB-003'] + [test_authentication()]
                st.session_state.audit_findings=findings
                save_audit(findings)
            except Exception as exc:
                st.error(f'Could not audit the local simulator: {exc}')
        findings=st.session_state.get('audit_findings',[])
        if findings:
            st.dataframe(pd.DataFrame(findings),hide_index=True,use_container_width=True)
            verified=sum(f['classification']=='Confirmed lab policy violation' for f in findings)
            st.metric('Confirmed simulated policy violations', verified)
            try:
                snapshot,events=fetch_telemetry_and_events()
                st.download_button('Download digital-twin evidence PDF',
                    data=make_security_pdf(findings,snapshot,events),
                    file_name='ViperAura_Digital_Twin_Evidence.pdf',mime='application/pdf')
            except Exception:
                st.download_button('Download digital-twin evidence PDF',
                    data=make_security_pdf(findings),file_name='ViperAura_Digital_Twin_Evidence.pdf',mime='application/pdf')
    st.caption('Two local training modes: secure (default) and intentionally misconfigured. Never expose the simulator beyond 127.0.0.1.')

with security_tab:
    st.subheader('Authorized Lab Network Assessment')
    st.warning('Only scan hosts or networks you own or are explicitly permitted to test. Satellite and third-party ground networks are out of scope.')
    target=st.text_input('Private IPv4 address or CIDR (maximum 16 addresses)',value='127.0.0.1')
    authorized=st.checkbox('I own this lab target or have explicit authorization to scan it.')
    if 'last_rows' not in st.session_state: st.session_state.last_rows=[]
    if 'last_target' not in st.session_state: st.session_state.last_target=''
    if st.button('Run lab-only scan',type='primary',disabled=not authorized):
        try:
            safe_target=validate_target(target)
            with st.spinner('Inspecting selected TCP ports on your authorized lab network...'):
                rows=scan(safe_target)
            st.session_state.last_rows=rows
            st.session_state.last_target=safe_target
            save_scan(safe_target,rows)
            st.success(f'Assessment finished: {len(rows)} open selected TCP port(s) detected.')
        except Exception as exc: st.error(str(exc))
    rows=st.session_state.last_rows
    if st.session_state.last_target:
        a,b,c=st.columns(3)
        a.metric('Open TCP ports',len(rows))
        b.metric('High review priority',sum(r['severity']=='High' for r in rows))
        c.metric('Confirmed vulnerabilities',0,help='This version does not perform authenticated vulnerability verification.')
        if rows:
            st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        else: st.info('No open selected TCP ports were found in the latest completed scan.')
        st.download_button('Download PDF assessment',data=make_pdf(st.session_state.last_target,rows),file_name='ViperAura_Orbital_Security_Report.pdf',mime='application/pdf')
    st.caption('Nmap uses a fixed, limited set of TCP ports and service-version probes. Findings are configuration-review suggestions, not verified exploits or CVEs.')
    st.info('To detect the simulated ground station, start ground_station.py in a second terminal, scan 127.0.0.1 and look for port 8080. An open port alone does not mean a vulnerability.')
with history_tab:
    data=history()
    if data:
        st.dataframe(pd.DataFrame([{'ID':a,'Timestamp UTC':b,'Target':c,'Open ports':len(__import__('json').loads(d))} for a,b,c,d in data]),hide_index=True,use_container_width=True)
    else: st.info('No local scan history yet.')
    audits=audit_history()
    st.markdown('**Digital-twin security audit history**')
    if audits:
        st.dataframe(pd.DataFrame([{'ID':a,'Timestamp UTC':b,'Policy checks':len(__import__('json').loads(d))} for a,b,d in audits]),hide_index=True,use_container_width=True)
    else: st.info('No local digital-twin audits yet.')
    st.caption('History is stored only in the local SQLite database in this project directory.')
