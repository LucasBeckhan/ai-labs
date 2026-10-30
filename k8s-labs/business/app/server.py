"""可控的网络监控API教学程序：无认证、不连接生产系统，不是正式服务模板。"""
import json
import os
from pathlib import Path
import signal
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from domain import load_json, summary

HERE = Path(__file__).resolve().parent
DEFAULT_FIXTURE = HERE.parent / 'fixtures' / 'operations.json'


class State:
    def __init__(self, config_path, data_path):
        self.config_path, self.data_path = config_path, data_path
        self.started = time.monotonic()
        self.warmup = float(os.environ.get('WARMUP_SECONDS', '3'))
        self.release = os.environ.get('RELEASE', 'v1')
        self.env_label = os.environ.get('ENV_LABEL', 'blue')
        self.tenant = os.environ.get('DEMO_TENANT', 'demo-a')
        self.draining = False
        self.lock = threading.Lock()
        self.requests = 0

    def config(self):
        return load_json(self.config_path)

    def ready(self):
        cfg = self.config()
        return (not self.draining and time.monotonic() - self.started >= self.warmup
                and cfg.get('dependency_ok') is True)


def create_server(host='0.0.0.0', port=8000, config_path=None, data_path=None):
    state = State(config_path or os.environ.get('CONFIG_PATH', '/config/settings.json'),
                  data_path or os.environ.get('DATA_PATH', str(DEFAULT_FIXTURE)))

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, code, data, content_type='application/json; charset=utf-8'):
            raw = (json.dumps(data, ensure_ascii=False) if isinstance(data, (dict, list)) else data).encode()
            self.send_response(code)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            path = urlsplit(self.path).path
            try:
                if path == '/healthz':
                    return self.send(200, {'alive': True})  # 不检查外部依赖
                if path == '/startupz':
                    started = time.monotonic() - state.started >= state.warmup
                    return self.send(200 if started else 503, {'started': started})
                if path == '/readyz':
                    ready = state.ready()
                    return self.send(200 if ready else 503, {'ready': ready})
                if path == '/metrics':
                    with state.lock:
                        count = state.requests
                    return self.send(200, '# TYPE cec_demo_business_requests_total counter\n'
                                     f'cec_demo_business_requests_total {count}\n',
                                     'text/plain; version=0.0.4; charset=utf-8')
                cfg = state.config()
                if path == '/config':
                    return self.send(200, {'env_label': state.env_label,
                                          'file_label': cfg['label'], 'release': state.release})
                if not state.ready():
                    return self.send(503, {'error': 'not_ready'})
                with state.lock:
                    state.requests += 1
                if path == '/work':
                    # 有界CPU负载，仅用于本机HPA练习；不是业务计算。
                    ms = max(0, min(100, int(parse_qs(urlsplit(self.path).query).get('ms', ['50'])[0])))
                    deadline = time.monotonic() + ms / 1000
                    while time.monotonic() < deadline:
                        pass
                    return self.send(200, {'work_ms': ms})
                data = load_json(state.data_path)
                if path == '/api/circuits':
                    return self.send(200, {'tenant_id': state.tenant, 'release': state.release,
                                           'label': cfg['label'],
                                           'circuits': [x for x in data['circuits'] if x['tenant_id'] == state.tenant]})
                if path == '/api/summary':
                    return self.send(200, summary(data, state.tenant, cfg['start'], cfg['end']))
                return self.send(404, {'error': 'not_found'})
            except (OSError, ValueError, KeyError) as exc:
                print(json.dumps({'event': 'request_failed', 'type': type(exc).__name__}), flush=True)
                return self.send(503, {'error': 'config_or_data_unavailable'})

    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = False
    server.state = state
    return server


def main():
    server = create_server(port=int(os.environ.get('PORT', '8000')))

    def terminate(signum, frame):
        if server.state.draining:
            return
        server.state.draining = True
        print('{"event":"sigterm","draining":true}', flush=True)
        # shutdown不能在serve_forever同线程直接调用。
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    print(json.dumps({'event': 'started', 'release': server.state.release}), flush=True)
    try:
        server.serve_forever(poll_interval=0.1)
    finally:
        server.server_close()
        print('{"event":"shutdown_complete"}', flush=True)


if __name__ == '__main__':
    main()
