#!/usr/bin/env python3
"""专用本地业务沙箱控制器；只操作kind-labs/cec-k8s-practice。"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
CONTEXT = 'kind-labs'
NAMESPACE = 'cec-k8s-practice'
OWNER_KEY = 'training.ai-labs/owner'
OWNER = 'cec-business-sandbox'
FAULTS = ('selector', 'port', 'readiness', 'image', 'pending', 'config', 'dependency', 'crash', 'oom')


def k(*args, payload=None, check=True, timeout=25):
    result = subprocess.run(['kubectl', '--context', CONTEXT, '--request-timeout=10s', *args],
                            input=payload, capture_output=True, text=True, timeout=timeout)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result


def ns(*args, **kwargs):
    return k('-n', NAMESPACE, *args, **kwargs)


def guard(create=False):
    result = k('get', 'namespace', NAMESPACE, '-o', 'json', check=False)
    if result.returncode:
        if create and '(NotFound)' in result.stderr:
            body = {'apiVersion': 'v1', 'kind': 'Namespace', 'metadata': {
                'name': NAMESPACE, 'labels': {OWNER_KEY: OWNER}}}
            k('create', '-f', '-', payload=json.dumps(body))
            return
        raise RuntimeError(result.stderr.strip())
    if json.loads(result.stdout)['metadata'].get('labels', {}).get(OWNER_KEY) != OWNER:
        raise RuntimeError('同名namespace不属于本沙箱，拒绝修改；请人工检查，不自动接管')


def apply_file(name):
    print(ns('apply', '-f', str(ROOT / 'manifests' / name)).stdout, end='')


def config(changes=None):
    settings = json.loads((ROOT / 'fixtures/settings.json').read_text())
    settings.update(changes or {})
    body = {'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {
        'name': 'demo-config', 'namespace': NAMESPACE},
        'data': {'ENV_LABEL': settings['label'], 'settings.json': json.dumps(settings)}}
    ns('apply', '-f', '-', payload=json.dumps(body))


def materialize():
    code_args = [f'--from-file={name}={ROOT / "app" / name}' for name in ('server.py', 'domain.py', 'report.py')]
    for name, args in [('demo-code', code_args), ('demo-data', [f'--from-file=operations.json={ROOT / "fixtures/operations.json"}'])]:
        manifest = ns('create', 'configmap', name, *args, '--dry-run=client', '-o', 'json').stdout
        ns('apply', '-f', '-', payload=manifest)
    config()


def wait_ready():
    print(ns('rollout', 'status', 'deployment/monitor-api', '--timeout=45s', timeout=55).stdout, end='')


def up(recover=False):
    guard(create=not recover)
    if recover:
        ns('delete', 'hpa/monitor-api', 'pod/demo-load', 'pod/consumer-oom', 'pod/collector-crash',
           '--ignore-not-found', '--wait=false')
    materialize()
    apply_file('api.yaml')
    if recover:
        ns('rollout', 'restart', 'deployment/monitor-api')
    wait_ready()
    print('沙箱已部署。下一步: python3 business/labctl.py verify')


def patch(kind, name, body):
    ns('patch', kind, name, '--type=merge', '-p', json.dumps(body))


def fault(name):
    guard()
    if name == 'selector':
        patch('service', 'monitor-api', {'spec': {'selector': {'app': 'missing-backend'}}})
    elif name == 'port':
        patch('service', 'monitor-api', {'spec': {'ports': [{'name': 'http', 'port': 80, 'targetPort': 8999}]}})
    elif name in {'readiness', 'image', 'pending'}:
        container = {'name': 'api'}
        if name == 'readiness':
            container['readinessProbe'] = {'httpGet': {'path': '/wrong-ready', 'port': 'http'}}
        if name == 'image':
            container['image'] = 'python:3.12-training-missing'
        if name == 'pending':
            # request<=limit，确保合法入库后由调度器拒绝，而非API先拒绝。
            container['resources'] = {'requests': {'cpu': '200', 'memory': '64Mi'},
                                      'limits': {'cpu': '200', 'memory': '128Mi'}}
        ns('patch', 'deployment', 'monitor-api', '--type=strategic', '-p',
           json.dumps({'spec': {'template': {'spec': {'containers': [container]}}}}))
    elif name == 'config':
        config({'label': 'green'})
    elif name == 'dependency':
        config({'dependency_ok': False})
    elif name in {'crash', 'oom'}:
        apply_file(name + '.yaml')
    print(f'已注入 {name}。先采证与手动修复，recover仅用于最后核对恢复。')


def ready_pod():
    pods = json.loads(ns('get', 'pods', '-l', 'app=monitor-api', '-o', 'json').stdout)['items']
    for pod in pods:
        if not pod['metadata'].get('deletionTimestamp') and any(
                c['type'] == 'Ready' and c['status'] == 'True' for c in pod.get('status', {}).get('conditions', [])):
            return pod['metadata']['name']
    raise RuntimeError('没有Ready的API Pod；检查Events、配置与探针')


def verify():
    guard()
    obj = json.loads(ns('get', 'deployment/monitor-api', '-o', 'json').stdout)
    expected = obj['spec']['replicas']
    status = obj.get('status', {})
    if (status.get('observedGeneration', 0) < obj['metadata']['generation'] or
        any(status.get(key, 0) != expected for key in ('updatedReplicas', 'readyReplicas', 'availableReplicas')) or
        status.get('replicas', 0) != expected):
        raise RuntimeError('Deployment尚未完成发布，不能只凭旧副本Ready认定恢复')
    slices = json.loads(ns('get', 'endpointslices', '-l', 'kubernetes.io/service-name=monitor-api', '-o', 'json').stdout)
    if not any(e.get('conditions', {}).get('ready') is True for s in slices['items'] for e in s.get('endpoints', [])):
        raise RuntimeError('Service没有Ready后端')
    pod = ready_pod()
    # 通过集群内Service访问，避免port-forward绕过selector/targetPort而造成假阳性。
    for path in ('/api/summary', '/api/circuits'):
        script = "import json,urllib.request; print(urllib.request.urlopen(" + repr('http://monitor-api' + path) + ",timeout=3).read().decode())"
        data = json.loads(ns('exec', pod, '--', 'python', '-c', script).stdout)
        if path.endswith('summary'):
            if data.get('raw_count') != 3 or data.get('unique_count') != 2 or data.get('event_ids') != ['E-001', 'E-002']:
                raise RuntimeError('业务统计口径不符合fixture')
        elif [x['circuit_id'] for x in data.get('circuits', [])] != ['C-A01', 'C-A02']:
            raise RuntimeError('业务线路不符合固定demo-a范围')
        print(json.dumps(data, ensure_ascii=False))
    print('PASS: 发布完成、Service后端和集群内业务请求/数值均正确。此检查不证明鉴权或生产高可用。')


def capture(directory):
    guard()
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    commands = {
        'objects.txt': ('get', 'deploy,rs,pods,svc,cm,pvc,jobs,cronjobs,hpa', '-o', 'wide'),
        'events.txt': ('get', 'events', '--sort-by=.metadata.creationTimestamp'),
        'deployment.txt': ('describe', 'deployment/monitor-api'),
        'pods.txt': ('describe', 'pods', '-l', 'training=cec-demo'),
        'pods.json': ('get', 'pods', '-l', 'training=cec-demo', '-o', 'json'),
        'endpoints.json': ('get', 'endpointslices', '-l', 'kubernetes.io/service-name=monitor-api', '-o', 'json'),
        'logs.txt': ('logs', '-l', 'app=monitor-api', '--prefix', '--tail=80'),
    }
    for file, command in commands.items():
        result = ns(*command, check=False)
        (path / file).write_text(result.stdout + result.stderr)
    print(f'证据已写入 {path.resolve()}，不采集Secret。')


def report():
    guard()
    apply_file('batch.yaml')
    name = 'security-report-' + str(time.time_ns())
    ns('create', 'job', name, '--from=cronjob/security-report')
    print(ns('wait', '--for=condition=complete', 'job/' + name, '--timeout=45s', timeout=55).stdout, end='')
    text = ns('logs', 'job/' + name).stdout
    lines = [json.loads(line) for line in text.splitlines() if line.startswith('{')]
    if not lines or lines[-1].get('unique_count') != 2 or lines[-1].get('raw_count') != 3:
        raise RuntimeError('Job完成但业务结果不正确')
    print(text, end='')
    print('PASS: Job完成且raw=3/unique=2；PVC中的归档不等于异地备份。')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    for action in ('up', 'verify', 'recover', 'status', 'report', 'clean'):
        sub.add_parser(action)
    sub.add_parser('fault').add_argument('name', choices=FAULTS)
    sub.add_parser('capture').add_argument('--output', default=str(ROOT / 'work' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')))
    args = parser.parse_args()
    try:
        if args.action in ('up', 'recover'):
            up(args.action == 'recover')
        elif args.action == 'fault':
            fault(args.name)
        elif args.action == 'verify':
            verify()
        elif args.action == 'capture':
            capture(args.output)
        elif args.action == 'report':
            report()
        elif args.action == 'clean':
            guard()
            print(ns('get', 'pvc', check=False).stdout)
            print('删除专用namespace，含练习PVC及模拟报告；不删除kind集群。')
            k('delete', 'namespace', NAMESPACE, '--wait=false')
        elif args.action == 'status':
            guard()
            print(ns('get', 'deploy,pods,svc,pvc,jobs,hpa', '-o', 'wide').stdout)
    except (RuntimeError, subprocess.TimeoutExpired, OSError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
