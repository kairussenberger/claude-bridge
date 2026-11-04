#!/usr/bin/env python3
"""Send Python code to the ClaudeBridge add-in running inside Fusion.
usage: fusion.py 'code'   |   fusion.py -f script.py   |   echo code | fusion.py
       fusion.py --ping"""
import sys, os, json, urllib.request, urllib.error

URL = 'http://127.0.0.1:47621/exec'
args = sys.argv[1:]
if args[:1] == ['--ping']:
    try:
        print(urllib.request.urlopen('http://127.0.0.1:47621/', timeout=3).read().decode())
    except Exception as e:
        sys.exit(f'bridge not reachable: {e}')
    sys.exit()
code = open(args[1]).read() if args[:1] == ['-f'] else (args[0] if args else sys.stdin.read())
token = open(os.path.expanduser('~/.fusion_bridge_token')).read().strip()
req = urllib.request.Request(URL, data=code.encode(), headers={'X-Token': token, 'X-Timeout': '300'})
try:
    resp = json.loads(urllib.request.urlopen(req, timeout=310).read())
except urllib.error.HTTPError as e:
    resp = json.loads(e.read())
except urllib.error.URLError as e:
    sys.exit(f'bridge not reachable (is ClaudeBridge running in Fusion?): {e}')
if resp.get('stdout'):
    print(resp['stdout'], end='')
if resp.get('result') is not None:
    print(json.dumps(resp['result'], indent=2) if not isinstance(resp['result'], str) else resp['result'])
if not resp.get('ok'):
    print(resp.get('error'), file=sys.stderr)
    sys.exit(1)
