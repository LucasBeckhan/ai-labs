"""纯业务函数，供监控API、批处理与离线测试复用。"""
from collections import Counter
from datetime import datetime
import json
from pathlib import Path


def timestamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('timezone required')
    return result


def load_json(path):
    return json.loads(Path(path).read_text())


def summary(data, tenant, start, end):
    begin, finish = timestamp(start), timestamp(end)
    if begin >= finish:
        raise ValueError('start must precede end')
    rows = [x for x in data['alerts'] if x['tenant_id'] == tenant
            and begin <= timestamp(x['occurred_at']) < finish]
    # 本fixture同ID内容相同；真实系统应定义版本与冲突处理，不能盲目最后到达胜出。
    unique = {x['event_id']: x for x in rows}
    return {'tenant_id': tenant, 'start': start, 'end': end,
            'raw_count': len(rows), 'unique_count': len(unique),
            'by_severity': dict(Counter(x['severity'] for x in unique.values())),
            'event_ids': sorted(unique), 'source_as_of': data['as_of']}
