"""业务训练参考：纯标准库、离线、只读模拟工具；不连接任何公司系统。

这里实现确定性的工具与 Workflow 基线，不声称是 LLM Agent 或生产服务。
实验要求学生把原有 Agent 决策循环接到这些工具，安全上下文不能交给模型填写。
"""
import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from pathlib import Path
import time

FIXTURE = Path(__file__).parent / 'fixtures' / 'operations.json'


class ToolError(Exception):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class Context:
    # 仅模拟已验证身份；生产必须来自认证中间件，不能从请求正文相信 tenant_id。
    tenant_id: str
    request_id: str
    scopes: frozenset = frozenset({'ops:read', 'kb:read'})


def timestamp(value):
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            raise ValueError('timezone required')
        return result
    except (AttributeError, TypeError, ValueError) as exc:
        raise ToolError('invalid_argument', '时间必须是带时区的 ISO8601') from exc


class Sandbox:
    def __init__(self, fixture=FIXTURE, faults=None):
        self.data = json.loads(Path(fixture).read_text())
        self.faults = faults or {}
        self.audit = []

    def call(self, ctx, name, args):
        """严格校验、租户授权、结构化错误；故障在本地注入，不由模型选择。"""
        started = time.monotonic()
        code = 'ok'
        try:
            if not isinstance(args, dict):
                raise ToolError('invalid_argument', 'args 必须是对象')
            tools = {
                'get_circuit': ({'circuit_id'}, 'ops:read', self._circuit),
                'list_alerts': ({'start', 'end'}, 'ops:read', self._alerts),
                'search_runbook': ({'query'}, 'kb:read', self._search),
            }
            if name not in tools:
                raise ToolError('unknown_tool', '工具不在允许清单')
            fields, scope, handler = tools[name]
            if set(args) != fields or any(type(v) is not str or not v or len(v) > 200 for v in args.values()):
                raise ToolError('invalid_argument', '参数缺失、多余、类型或长度错误')
            if scope not in ctx.scopes:
                raise ToolError('forbidden', '当前身份无此工具权限')
            fault = self.faults.get(name)
            if fault in {'timeout', 'rate_limited'}:
                # 直接返回模拟故障，不实际阻塞线程，也不声称实现了超时控制。
                raise ToolError(fault, '模拟依赖失败')
            value = handler(ctx, args)
            return {'ok': True, 'data': value, 'source': 'synthetic-fixture',
                    'as_of': self.data['as_of'], 'request_id': ctx.request_id}
        except ToolError as exc:
            code = exc.code
            return {'ok': False, 'error': {'code': code, 'message': str(exc),
                    'retryable': code in {'timeout', 'rate_limited'}}, 'request_id': ctx.request_id}
        finally:
            # 不记录原文、参数和返回内容，避免把客户数据塞入审计日志。
            self.audit.append({'request_id': ctx.request_id, 'tenant_id': ctx.tenant_id,
                               'tool': name, 'code': code,
                               'duration_ms': round((time.monotonic() - started) * 1000, 3)})

    def _circuit(self, ctx, args):
        found = next((x.copy() for x in self.data['circuits']
                      if x['tenant_id'] == ctx.tenant_id and x['circuit_id'] == args['circuit_id']), None)
        if found is None:
            # 外部不区分不存在与越权对象，避免枚举别的租户资产。
            raise ToolError('not_found', '未找到可访问对象')
        age = timestamp(self.data['as_of']) - timestamp(found['observed_at'])
        found['stale'] = age > timedelta(minutes=5) or age < timedelta(0)
        return found

    def _alerts(self, ctx, args):
        start, end = timestamp(args['start']), timestamp(args['end'])
        if not start < end or end - start > timedelta(days=7):
            raise ToolError('invalid_argument', '窗口必须递增且不超过7天')
        records = [x for x in self.data['alerts'] if x['tenant_id'] == ctx.tenant_id
                   and start <= timestamp(x['occurred_at']) < end]
        unique = {x['event_id']: x for x in records}
        return {'raw_count': len(records), 'unique_count': len(unique),
                'event_ids': sorted(unique), 'window': '[start,end)'}

    def _search(self, ctx, args):
        # 关键词基线，不是向量检索；先做 ACL/有效版本过滤，再匹配。
        query = args['query'].strip()
        return [x.copy() for x in self.data['documents'] if x['tenant_id'] == ctx.tenant_id
                and x['valid'] and query and query in x['title']][:3]


def workflow(sandbox, ctx, circuit_id):
    result = sandbox.call(ctx, 'get_circuit', {'circuit_id': circuit_id})
    if not result['ok']:
        return {'status': 'needs_review', 'evidence': [], 'error': result['error']['code']}
    record = result['data']
    evidence = [{'source': 'get_circuit', 'circuit_id': circuit_id,
                 'observed_at': record['observed_at'], 'loss_pct': record['loss_pct']}]
    if record['stale']:
        return {'status': 'needs_review', 'evidence': evidence, 'reason': 'stale_evidence'}
    kb = sandbox.call(ctx, 'search_runbook', {'query': '链路丢包'})
    return {'status': 'draft', 'evidence': evidence,
            'citations': [x['doc_id'] for x in kb.get('data', [])],
            'finding': '观测到丢包升高，根因待确认' if record['loss_pct'] > 1 else '当前样本未见明显丢包',
            'next_step': '人工核对接口计数、近期变更与对端状态；不自动执行变更'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', choices=['network', 'report', 'timeout', 'cross-tenant'], default='network')
    args = parser.parse_args()
    sandbox = Sandbox(faults={'get_circuit': 'timeout'} if args.scenario == 'timeout' else {})
    ctx = Context('demo-a', 'offline-demo-001')
    if args.scenario == 'report':
        result = sandbox.call(ctx, 'list_alerts', {'start': '2026-10-28T00:00:00Z', 'end': '2026-10-28T02:00:00Z'})
    else:
        result = workflow(sandbox, ctx, 'C-B01' if args.scenario == 'cross-tenant' else 'C-A01')
    print(json.dumps({'result': result, 'audit': sandbox.audit}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
