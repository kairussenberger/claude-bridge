# ClaudeBridge: runs Python sent over localhost on Fusion's main thread.
# POST http://127.0.0.1:47621/exec  header X-Token: <~/.fusion_bridge_token>  body = python code
# The code sees adsk, app, ui, design; assign to `result` to return a value; print() is captured.
import adsk.core, adsk.fusion, traceback, threading, json, io, os, secrets, contextlib, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 47621
EVENT_ID = 'ClaudeBridgeExec'
TOKEN_FILE = os.path.expanduser('~/.fusion_bridge_token')

app = adsk.core.Application.get()
ui = app.userInterface
_handlers, _pending, _server, _event = [], {}, None, None
_scope = {}  # persists between calls, so helpers can be defined once


def _run(code):
    out = io.StringIO()
    g = _scope
    g.update(adsk=adsk, app=app, ui=ui,
             design=adsk.fusion.Design.cast(app.activeProduct), result=None)
    try:
        with contextlib.redirect_stdout(out):
            exec(compile(code, '<claude>', 'exec'), g)
        res = g.get('result')
        try:
            json.dumps(res)
        except TypeError:
            res = repr(res)
        return {'ok': True, 'stdout': out.getvalue(), 'result': res}
    except Exception:
        return {'ok': False, 'stdout': out.getvalue(), 'error': traceback.format_exc()}


class _ExecHandler(adsk.core.CustomEventHandler):
    def notify(self, args):
        job = _pending.get(args.additionalInfo)
        if job:
            job['resp'] = _run(job['code'])
            job['done'].set()


class _Http(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(200, {'ok': True, 'bridge': 'ClaudeBridge'})

    def do_POST(self):
        if self.headers.get('X-Token') != _token:
            return self._send(403, {'ok': False, 'error': 'bad token'})
        code = self.rfile.read(int(self.headers.get('Content-Length', 0))).decode()
        jid = uuid.uuid4().hex
        job = {'code': code, 'done': threading.Event(), 'resp': None}
        _pending[jid] = job
        app.fireCustomEvent(EVENT_ID, jid)
        timeout = float(self.headers.get('X-Timeout', 120))
        finished = job['done'].wait(timeout)
        _pending.pop(jid, None)
        if not finished:
            return self._send(504, {'ok': False, 'error': f'timed out after {timeout}s (Fusion busy or modal dialog open?)'})
        self._send(200, job['resp'])


def _load_token():
    if os.path.exists(TOKEN_FILE):
        return open(TOKEN_FILE).read().strip()
    t = secrets.token_hex(16)
    with open(TOKEN_FILE, 'w') as f:
        f.write(t)
    os.chmod(TOKEN_FILE, 0o600)
    return t


def run(context):
    global _server, _event, _token
    try:
        _token = _load_token()
        _event = app.registerCustomEvent(EVENT_ID)
        h = _ExecHandler()
        _event.add(h)
        _handlers.append(h)
        _server = ThreadingHTTPServer(('127.0.0.1', PORT), _Http)
        threading.Thread(target=_server.serve_forever, daemon=True).start()
        app.log(f'ClaudeBridge listening on 127.0.0.1:{PORT}')
    except Exception:
        ui.messageBox('ClaudeBridge failed to start:\n' + traceback.format_exc())


def stop(context):
    global _server
    try:
        if _server:
            _server.shutdown()
            _server.server_close()
            _server = None
        for h in _handlers:
            _event.remove(h)
        _handlers.clear()
        app.unregisterCustomEvent(EVENT_ID)
    except Exception:
        pass
