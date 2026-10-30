import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sandbox import Context, Sandbox, workflow


class ToolContractTests(unittest.TestCase):
    def setUp(self):
        self.sb = Sandbox()
        self.ctx = Context('demo-a', 'test-001')

    def test_normal_evidence_is_not_root_cause(self):
        result = workflow(self.sb, self.ctx, 'C-A01')
        self.assertEqual(result['status'], 'draft')
        self.assertEqual(result['evidence'][0]['loss_pct'], 8.5)
        self.assertEqual(result['citations'], ['KB-001'])
        self.assertIn('根因待确认', result['finding'])

    def test_no_cross_tenant_leak(self):
        result = self.sb.call(self.ctx, 'get_circuit', {'circuit_id': 'C-B01'})
        self.assertFalse(result['ok'])
        self.assertEqual(result['error']['code'], 'not_found')
        self.assertNotIn('北京', str(result))

    def test_model_cannot_supply_tenant(self):
        result = self.sb.call(self.ctx, 'get_circuit', {'circuit_id': 'C-B01', 'tenant_id': 'demo-b'})
        self.assertEqual(result['error']['code'], 'invalid_argument')

    def test_missing_scope(self):
        ctx = Context('demo-a', 'test-002', frozenset())
        result = self.sb.call(ctx, 'get_circuit', {'circuit_id': 'C-A01'})
        self.assertEqual(result['error']['code'], 'forbidden')

    def test_unknown_write_tool(self):
        result = self.sb.call(self.ctx, 'restart_device', {'circuit_id': 'C-A01'})
        self.assertEqual(result['error']['code'], 'unknown_tool')

    def test_duplicate_and_window(self):
        result = self.sb.call(self.ctx, 'list_alerts', {'start': '2026-10-28T00:00:00Z', 'end': '2026-10-28T02:00:00Z'})['data']
        self.assertEqual(result['raw_count'], 3)
        self.assertEqual(result['unique_count'], 2)
        self.assertEqual(result['event_ids'], ['E-001', 'E-002'])

    def test_invalid_time_range(self):
        for start, end in [('2026-10-28', '2026-10-29'), ('2026-10-28T02:00:00Z', '2026-10-28T00:00:00Z')]:
            with self.subTest(start=start):
                result = self.sb.call(self.ctx, 'list_alerts', {'start': start, 'end': end})
                self.assertEqual(result['error']['code'], 'invalid_argument')

    def test_stale_observation(self):
        self.sb.data['circuits'][0]['observed_at'] = '2026-10-27T01:58:00Z'
        result = workflow(self.sb, self.ctx, 'C-A01')
        self.assertEqual(result['reason'], 'stale_evidence')

    def test_dependency_timeout_not_healthy(self):
        sb = Sandbox(faults={'get_circuit': 'timeout'})
        result = workflow(sb, self.ctx, 'C-A01')
        self.assertEqual(result['status'], 'needs_review')
        self.assertEqual(result['evidence'], [])

    def test_filtered_retrieval(self):
        result = self.sb.call(self.ctx, 'search_runbook', {'query': '手册'})
        self.assertEqual(result['data'], [])

    def test_wrong_argument_type(self):
        result = self.sb.call(self.ctx, 'get_circuit', {'circuit_id': 1})
        self.assertEqual(result['error']['code'], 'invalid_argument')

    def test_audit_does_not_capture_payload(self):
        self.sb.call(self.ctx, 'get_circuit', {'circuit_id': 'C-A01'})
        self.assertEqual(self.sb.audit[0]['code'], 'ok')
        self.assertNotIn('C-A01', str(self.sb.audit))
        self.assertNotIn('8.5', str({k:v for k,v in self.sb.audit[0].items() if k != 'duration_ms'}))


if __name__ == '__main__':
    unittest.main()
