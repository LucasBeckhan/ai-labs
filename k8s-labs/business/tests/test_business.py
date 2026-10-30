import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from domain import load_json, summary
from report import archive
from server import create_server, DEFAULT_FIXTURE


class BusinessTests(unittest.TestCase):
    def test_local_default_fixture_path(self):
        self.assertTrue(DEFAULT_FIXTURE.is_file())

    def test_correct_tenant_window_and_deduplication(self):
        data = load_json(ROOT / 'fixtures/operations.json')
        result = summary(data, 'demo-a', '2026-10-28T00:00:00Z', '2026-10-28T02:00:00Z')
        self.assertEqual((result['raw_count'], result['unique_count']), (3, 2))
        self.assertEqual(result['event_ids'], ['E-001', 'E-002'])
        self.assertEqual(result['by_severity'], {'high': 1, 'medium': 1})

    def test_timezone_and_next_window(self):
        data = load_json(ROOT / 'fixtures/operations.json')
        result = summary(data, 'demo-a', '2026-10-28T10:00:00+08:00', '2026-10-28T11:00:00+08:00')
        self.assertEqual(result['event_ids'], ['E-004'])

    def test_invalid_window(self):
        data = load_json(ROOT / 'fixtures/operations.json')
        with self.assertRaises(ValueError):
            summary(data, 'demo-a', '2026-10-28', '2026-10-29')
        with self.assertRaises(ValueError):
            summary(data, 'demo-a', '2026-10-28T02:00:00Z', '2026-10-28T00:00:00Z')

    def test_archive_repeated_and_incomplete(self):
        with tempfile.TemporaryDirectory() as directory:
            report = {'count': 2}
            status, name = archive(report, directory)
            self.assertEqual(status, 'created')
            self.assertEqual(archive(report, directory)[0], 'existing')
            (Path(directory) / name).write_text('partial')
            with self.assertRaises(ValueError):
                archive(report, directory)


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config = Path(self.temp.name) / 'settings.json'
        self.config.write_text((ROOT / 'fixtures/settings.json').read_text())
        with patch.dict(os.environ, {'WARMUP_SECONDS': '0', 'ENV_LABEL': 'blue'}):
            self.server = create_server('127.0.0.1', 0, self.config, ROOT / 'fixtures/operations.json')
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': .01}, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def get(self, path):
        with urllib.request.urlopen(self.url + path, timeout=2) as response:
            return json.load(response)

    def test_service_business_response(self):
        self.assertEqual(self.get('/api/summary')['unique_count'], 2)
        self.assertEqual(len(self.get('/api/circuits')['circuits']), 2)

    def test_file_hot_reload_env_snapshot(self):
        cfg = json.loads(self.config.read_text())
        cfg['label'] = 'green'
        self.config.write_text(json.dumps(cfg))
        result = self.get('/config')
        self.assertEqual(result['file_label'], 'green')
        self.assertEqual(result['env_label'], 'blue')

    def test_dependency_failure_not_liveness_failure(self):
        cfg = json.loads(self.config.read_text())
        cfg['dependency_ok'] = False
        self.config.write_text(json.dumps(cfg))
        self.assertTrue(self.get('/healthz')['alive'])
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.get('/readyz')
        self.assertEqual(cm.exception.code, 503)
        cm.exception.close()

    def test_malformed_config_is_not_healthy(self):
        self.config.write_text('not-json')
        self.assertTrue(self.get('/healthz')['alive'])
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.get('/api/summary')
        self.assertEqual(cm.exception.code, 503)
        cm.exception.close()

    def test_draining_stops_business(self):
        self.server.state.draining = True
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.get('/api/circuits')
        self.assertEqual(cm.exception.code, 503)
        cm.exception.close()


class CLIGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('labctl', ROOT / 'labctl.py')
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_refuse_foreign_namespace(self):
        result = subprocess.CompletedProcess([], 0, json.dumps({'metadata': {'labels': {}}}), '')
        with patch.object(self.module, 'k', return_value=result):
            with self.assertRaises(RuntimeError):
                self.module.guard()

    def test_fixed_context_namespace(self):
        with patch.object(self.module.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')) as run:
            self.module.ns('get', 'pods')
            command = run.call_args.args[0]
            self.assertIn('kind-labs', command)
            self.assertIn('cec-k8s-practice', command)
            self.assertNotIn('shell', run.call_args.kwargs)


if __name__ == '__main__':
    unittest.main()
