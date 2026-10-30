"""安全周报的短窗口统计训练：输出JSON；可选PVC文件归档，无外部发送。"""
import hashlib
import json
import os
from pathlib import Path

from domain import load_json, summary


def archive(report, directory):
    """无覆盖写，单进程演示；非分布式事务/崩溃一致性实现。"""
    payload = json.dumps(report, ensure_ascii=False, sort_keys=True)
    key = hashlib.sha256(payload.encode()).hexdigest()[:24]
    destination = Path(directory) / f'{key}.json'
    try:
        with destination.open('x') as file:
            file.write(payload)
    except FileExistsError:
        if destination.read_text() != payload:
            raise ValueError('incomplete or conflicting archive; manual recovery required')
        return 'existing', destination.name
    return 'created', destination.name


def main():
    if os.environ.get('FAIL_REPORT') == '1':
        raise RuntimeError('simulated report failure')
    cfg = load_json(os.environ.get('CONFIG_PATH', '/config/settings.json'))
    report = summary(load_json(os.environ.get('DATA_PATH', '/data/operations.json')),
                     os.environ.get('DEMO_TENANT', 'demo-a'), cfg['start'], cfg['end'])
    if os.environ.get('REPORT_DIR'):
        status, key = archive(report, os.environ['REPORT_DIR'])
        print(json.dumps({'archive': status, 'file': key}), flush=True)
    print(json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
