from io import BytesIO
from datetime import datetime, timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.utils import simpleSplit
from xml.sax.saxutils import escape

def make_pdf(target, rows):
    buffer=BytesIO()
    doc=SimpleDocTemplate(buffer,pagesize=letter,rightMargin=45,leftMargin=45)
    styles=getSampleStyleSheet()
    story=[Paragraph('ViperAura Orbital Security — Lab Assessment',styles['Title']),Spacer(1,12),Paragraph('Target: '+escape(target),styles['Normal']),Paragraph('Generated (UTC): '+datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M'),styles['Normal']),Spacer(1,12),Paragraph('Scope: Authorized local/private IPv4 lab only. Port observations and review suggestions are NOT verified vulnerabilities.',styles['BodyText']),Spacer(1,16)]
    if not rows:
        story.append(Paragraph('No open ports observed among the selected ports. This does not prove the target is secure.',styles['BodyText']))
    else:
        data=[['Host','Port','Service','Review priority']]
        for row in rows:
            data.append([row['host'],str(row['port']),row['service'],row['severity']])
        table=Table(data,repeatRows=1,colWidths=[150,60,160,115])
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#242946')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.whitesmoke,colors.white]),('GRID',(0,0),(-1,-1),0.35,colors.lightgrey),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
        story.append(table)
        story.append(Spacer(1,15))
        for row in rows:
            line=f"{row['host']}:{row['port']} — {row['service']} ({row['severity']})"
            story.append(Paragraph(escape(line),styles['Heading4']))
            story.append(Paragraph(escape(row['finding']),styles['BodyText']))
            story.append(Spacer(1,7))
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def make_security_pdf(findings, telemetry=None, events=None):
    """Export separately scoped lab policy checks and synthetic monitoring events."""
    buffer=BytesIO()
    doc=SimpleDocTemplate(buffer,pagesize=letter,rightMargin=46,leftMargin=46)
    styles=getSampleStyleSheet()
    story=[Paragraph('ViperAura Orbital Security — Digital Twin Evidence Report',styles['Title']),Spacer(1,12),
        Paragraph('Generated (UTC): '+datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M'),styles['Normal']),Spacer(1,10),
        Paragraph('Scope: ViperAura local-only synthetic ground station (127.0.0.1:8080). Findings are lab policy checks, NOT real satellite weaknesses or authenticated CVEs.',styles['BodyText']),Spacer(1,12)]
    for item in findings:
        story.append(Paragraph(escape(f"{item['id']} | {item['title']} | {item['severity']}"),styles['Heading3']))
        for key in ['classification','evidence','remediation']:
            story.append(Paragraph(escape(key.title()+': '+item[key]),styles['BodyText']))
        story.append(Spacer(1,8))
    if telemetry:
        story.append(Paragraph('Synthetic Telemetry Snapshot',styles['Heading2']))
        import json
        story.append(Paragraph(escape(json.dumps(telemetry,sort_keys=True)),styles['BodyText']))
    if events is not None:
        story.append(Spacer(1,10))
        story.append(Paragraph('Recent Synthetic Authentication Events',styles['Heading2']))
        for event in events[:25]:
            story.append(Paragraph(escape(f"{event['timestamp_utc']} | {event['identity']} | {event['event']} | {event['result']}"),styles['BodyText']))
    doc.build(story)
    return buffer.getvalue()
