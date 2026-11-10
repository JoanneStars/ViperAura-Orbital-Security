"""Diagram of the simulated satellite / local network boundary."""
import plotly.graph_objects as go


def topology_figure(simulator_online=False, scanner_findings=None):
    scanner_findings = scanner_findings or []
    identified = any(row.get('port') == 8080 and row.get('host')=='127.0.0.1' for row in scanner_findings)
    nodes = [
        ('🛰 Simulated satellite',.5,.85,'#b78aff'),
        ('📡 Virtual RF link',.5,.62,'#6a85c1'),
        ('🖥 Ground station (localhost:8080)',.22,.38,'#5ed4ae' if simulator_online else '#9ca5bc'),
        ('🔎 Lab Nmap scanner',.78,.38,'#56c9f4'),
        ('📊 ViperAura dashboard',.5,.13,'#ff83c6')
    ]
    fig=go.Figure()
    for a,b,dash in [(0,1,'dot'),(1,2,'dot'),(2,3,'solid'),(2,4,'solid'),(3,4,'solid')]:
        fig.add_trace(go.Scatter(x=[nodes[a][1],nodes[b][1]],y=[nodes[a][2],nodes[b][2]],
             mode='lines',line=dict(color='#526caa' if dash=='solid' else '#825cb4',width=2,dash=dash),
             hoverinfo='skip',showlegend=False))
    for label,x,y,color in nodes:
        fig.add_trace(go.Scatter(x=[x],y=[y],mode='markers+text',text=[label],
            textposition='bottom center',textfont=dict(color='#edf3ff',size=12),
            marker=dict(size=21,color=color,line=dict(color='#d0deff',width=1)),
            hoverinfo='text',showlegend=False))
    fig.update_layout(height=465,paper_bgcolor='#091229',plot_bgcolor='#091229',
        margin=dict(l=25,r=25,t=25,b=30), xaxis=dict(visible=False,range=[-.1,1.1]),
        yaxis=dict(visible=False,range=[-.05,1.05]))
    return fig


def simulator_health():
    from urllib.request import urlopen
    try:
        with urlopen('http://127.0.0.1:8080/health',timeout=1.25) as response:
            import json
            item=json.loads(response.read(2048))
            return response.status == 200 and item.get('system')=='ViperAura simulated ground station'
    except Exception:
        return False
