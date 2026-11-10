"""Orbital position prediction and offline Earth globe for the ViperAura lab."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import numpy as np
import plotly.graph_objects as go

EARTH_RADIUS_KM = 6371.0
PALETTE = ['#b78aff','#ff72ca','#56c9f4','#f7bb72','#92e5b9']


def demo_positions(samples=180, altitude_km=550, inclination=51.6, phase=0):
    t = np.linspace(0, 2*np.pi, samples) + phase
    r = EARTH_RADIUS_KM + altitude_km
    inc = np.radians(inclination)
    return np.array([r*np.cos(t), r*np.sin(t)*np.cos(inc), r*np.sin(t)*np.sin(inc)])


def from_tle(text):
    """Propagate one public TLE using Skyfield, no satellite communications."""
    from skyfield.api import EarthSatellite, load
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) == 3 and not lines[0].startswith('1 '):
        name, line1, line2 = lines
    elif len(lines) == 2:
        name, (line1, line2) = 'User TLE', lines
    else:
        raise ValueError('Provide a satellite name (optional) plus exactly two TLE lines.')
    if not line1.startswith('1 ') or not line2.startswith('2 '):
        raise ValueError('TLE lines must begin with 1 and 2 respectively.')
    if len(line1) < 60 or len(line2) < 60 or line1[2:7] != line2[2:7]:
        raise ValueError('TLE is incomplete or satellite identifiers do not match.')
    ts = load.timescale()
    sat = EarthSatellite(line1, line2, name, ts)
    age = abs((datetime.now(timezone.utc) - sat.epoch.utc_datetime()).total_seconds()) / 86400
    now = datetime.now(timezone.utc)
    dates = [now + timedelta(minutes=i) for i in range(94)]
    positions = np.asarray(sat.at(ts.from_datetimes(dates)).xyz.km)
    if not np.isfinite(positions).all():
        raise ValueError('Orbit prediction failed. Check that the TLE is valid and current.')
    return positions, name, age


def parse_multiple_tles(text, limit=5):
    """Accept a sequence of 2-line or name+2-line TLE records."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    groups = []
    i = 0
    while i < len(lines):
        if lines[i].startswith('1 '):
            if i + 1 >= len(lines): raise ValueError('Missing TLE line 2.')
            groups.append('\n'.join(lines[i:i+2])); i += 2
        else:
            if i + 2 >= len(lines): raise ValueError('Missing TLE data after satellite name.')
            groups.append('\n'.join(lines[i:i+3])); i += 3
        if len(groups) > limit: raise ValueError(f'Maximum {limit} satellite TLE records at once.')
    return groups


def _globe():
    """Render an offline, land/ocean colored geographic sphere."""
    lat = np.linspace(-90,90,181)
    lon = np.linspace(-180,180,361)
    lonr, latr = np.meshgrid(np.radians(lon),np.radians(lat))
    x = EARTH_RADIUS_KM*np.cos(latr)*np.cos(lonr)
    y = EARTH_RADIUS_KM*np.cos(latr)*np.sin(lonr)
    z = EARTH_RADIUS_KM*np.sin(latr)
    mask = np.load(Path(__file__).with_name('earth_land_mask.npz'))['mask']
    # Ocean, coast and land colors; coast detail comes from Natural Earth low-res coastline.
    shade = .04*np.sin(7*lonr)*np.cos(4*latr)
    color = np.where(mask > 0, .68 + .12*np.cos(latr*2), .13 + shade)
    return go.Surface(x=x,y=y,z=z,surfacecolor=color, cmin=0,cmax=1,
        colorscale=[[0,'#05142e'],[.15,'#0e3c77'],[.35,'#1d669c'],[.49,'#2f8eac'],
                    [.50,'#2f6759'],[.7,'#4c9a76'],[.82,'#7dae76'],[1,'#e5e3d6']],
        showscale=False, hoverinfo='skip', name='Earth')


def orbital_figure(xyz, name='Demonstration satellite'):
    return multi_orbital_figure([(xyz,name)])


def multi_orbital_figure(orbit_data):
    fig=go.Figure()
    fig.add_trace(_globe())
    for i,(xyz,name) in enumerate(orbit_data):
        color=PALETTE[i % len(PALETTE)]
        fig.add_trace(go.Scatter3d(x=xyz[0],y=xyz[1],z=xyz[2],mode='lines',
            line=dict(color=color,width=5),name=f'{name} — trajectory',hovertemplate=name+'<extra></extra>'))
        fig.add_trace(go.Scatter3d(x=[xyz[0,0]],y=[xyz[1,0]],z=[xyz[2,0]],
            mode='markers+text',text=[name],textposition='top center',
            textfont=dict(size=11,color='#eaf1ff'),marker=dict(size=7,color=color),
            name=name,hovertemplate=name+'<extra></extra>'))
    fig.update_layout(paper_bgcolor='#080d20',plot_bgcolor='#080d20',
        font=dict(color='#eaf1ff'),margin=dict(l=0,r=0,t=16,b=0),height=610,
        scene=dict(bgcolor='#080d20',aspectmode='data',
             xaxis=dict(visible=False),yaxis=dict(visible=False),zaxis=dict(visible=False),
             camera=dict(eye=dict(x=1.65,y=1.55,z=.9))),
        legend=dict(orientation='h',y=-.06,font=dict(size=11)))
    return fig
