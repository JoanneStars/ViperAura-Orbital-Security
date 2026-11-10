"""Restricted, opt-in lab-only network inventory via local Nmap installation."""
import ipaddress
import shutil
import subprocess
import xml.etree.ElementTree as ET

ALLOWED_PORTS = '21,22,23,53,80,139,443,445,3389,8080,8443'

def validate_target(target):
    """Only IPv4 loopback/private target addresses, max 16 addresses."""
    target = target.strip()
    try:
        net = ipaddress.ip_network(target, strict=False)
    except ValueError as exc:
        raise ValueError('Enter an IPv4 address or a small IPv4 CIDR (for example 192.168.56.10).') from exc
    if net.version != 4 or net.num_addresses > 16:
        raise ValueError('Only IPv4 lab ranges of up to 16 addresses are supported.')
    # Exclude shared/CGNAT, special purpose, link-local, multicast and broad ranges.
    if not all(ip.is_loopback or (ip.is_private and not ip.is_link_local and not ip.is_reserved and not ip.is_multicast and not ip.is_unspecified) for ip in net):
        raise ValueError('Only private or loopback IPv4 lab targets are permitted. Public IPs are blocked.')
    # Ensure the supplied prefix does not contain off-limits hosts (loop above covers this).
    return str(net)

def assess(port, service):
    """Heuristics for configuration review only; not vulnerability confirmation."""
    if port == 23:
        return 'High', 'Telnet commonly lacks transport encryption; confirm exposure and disable if unnecessary.'
    if port in (21,):
        return 'Medium', 'Review FTP authentication and plaintext transport; prefer encrypted alternatives.'
    if port in (139,445,3389):
        return 'Medium', 'Review access controls, patch status and segmentation for this service.'
    if port in (80,8080):
        return 'Low', 'Review HTTP transport security and application configuration.'
    return 'Info', 'Open service observed; review necessity, access restrictions and versions.'

def scan(target, timeout=65):
    target = validate_target(target)
    if not shutil.which('nmap'):
        raise RuntimeError('Nmap executable is not installed or not available on PATH.')
    cmd = ['nmap','-sT','-sV','--version-light','-Pn','-n','--max-retries','1','--host-timeout','45s','-p',ALLOWED_PORTS,'-oX','-',target]
    try:
        result = subprocess.run(cmd,capture_output=True,text=True,timeout=timeout,check=False)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError('Nmap timed out.') from exc
    if result.returncode != 0:
        raise RuntimeError((result.stderr or 'Nmap returned an error.')[:600])
    root = ET.fromstring(result.stdout)
    rows=[]
    for host in root.findall('host'):
        addr = host.find('address')
        if addr is None: continue
        host_ip=addr.get('addr','')
        for port_node in host.findall('./ports/port'):
            state=port_node.find('state')
            if state is None or state.get('state') != 'open': continue
            service=port_node.find('service')
            p=int(port_node.get('portid'))
            service_name=service.get('name','unknown') if service is not None else 'unknown'
            product=service.get('product','') if service is not None else ''
            version=service.get('version','') if service is not None else ''
            severity, note = assess(p,service_name)
            rows.append(dict(host=host_ip,port=p,protocol=port_node.get('protocol','tcp'),service=service_name,version=' '.join(filter(None,[product,version])),severity=severity,finding=note,status='Review required — unverified'))
    return rows
