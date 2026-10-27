"""Read-only pilot checker. Mechanical validity never certifies semantic truth."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import unquote, urlsplit


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def without_code(text):
    return re.sub(r'^(`{3,}|~{3,}).*?^\1[^\n]*$', '', text, flags=re.M | re.S)


def tables(text):
    header = None
    for line in without_code(text).splitlines():
        if not line.strip().startswith('|'):
            header = None
            continue
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if all(re.fullmatch(r':?-+:?', cell) for cell in cells):
            continue
        if header is None:
            header = cells
        else:
            if len(cells) != len(header) or not all(cells):
                raise ValueError('Malformed or empty index table cell')
            yield dict(zip(header, cells))


def link_target(value):
    match = re.fullmatch(r'\[[^\]]+\]\(([^)]+)\)', value)
    if not match:
        raise ValueError('Source must be a Markdown link')
    return match.group(1)


def local_target(root, base, value):
    url = urlsplit(value)
    if url.scheme or url.netloc or Path(unquote(url.path)).is_absolute():
        raise ValueError('OUTSIDE_ROOT')
    candidate = base / unquote(url.path) if url.path else base
    if not candidate.resolve().is_relative_to(root):
        raise ValueError('OUTSIDE_ROOT')
    current = candidate
    while current != root and current.is_relative_to(root):
        if current.is_symlink():
            raise ValueError('SYMLINK')
        current = current.parent
    return candidate.resolve(), unquote(url.fragment)


def anchors(text):
    result = set(re.findall(r'<a\s+id=[\"\']([^\"\']+)', text, re.I))
    counts = Counter()
    for line in without_code(text).splitlines():
        match = re.match(r'^#{1,6}\s+(.+?)\s*#*$', line)
        if match:
            slug = re.sub(r'[^\w\-\s]', '', match.group(1).lower()).replace(' ', '-')
            n = counts[slug]
            counts[slug] += 1
            result.add(slug if not n else f'{slug}-{n}')
    return result


def inactive(text):
    return bool(re.search(r'^#\s+INVALID\b|^(?:Status|Document-Role):\s*(?:INVALID|HISTORICAL)', without_code(text), re.M | re.I))


def check(root):
    findings = []

    def fail(code, path='', **details):
        findings.append({'code': code, 'path': str(path), **details})

    index = root / 'CODEX_START_HERE.md'
    if index.is_symlink():
        raise ValueError('Index must not be a symlink')
    text = index.read_text(encoding='utf-8')
    if '<!-- doc-governance:v1 -->' not in text:
        raise ValueError('Missing doc-governance:v1 marker')
    rows = list(tables(text))
    permitted = [{'Topic', 'Category', 'Source'}, {'Historical file', 'SHA256'}, {'Topic', 'Dependency', 'Reviewed SHA256'}]
    if any(set(row) not in permitted for row in rows):
        raise ValueError('Unknown index table schema')
    owners = [row for row in rows if 'Source' in row]
    if not owners:
        raise ValueError('No current topics declared')
    for topic, n in Counter(row['Topic'] for row in owners).items():
        if n > 1:
            fail('DUPLICATE_TOPIC', topic=topic)
    historical = {}
    for row in rows:
        if 'Historical file' not in row:
            continue
        path = row['Historical file']
        try:
            resolved, fragment = local_target(root, root, path)
            normalized = resolved.relative_to(root).as_posix()
            if fragment or path != normalized:
                fail('NON_CANONICAL_HISTORY', path)
            path = normalized
        except ValueError as exc:
            fail(str(exc), path)
            continue
        if path in historical:
            fail('DUPLICATE_HISTORY', path)
        historical[path] = row['SHA256']
    registered = set()
    snapshot = {'CODEX_START_HERE.md': digest(index)}

    def validate(base, target, source):
        try:
            path, fragment = local_target(root, base, target)
        except ValueError as exc:
            fail(str(exc), source, target=target)
            return None
        rel = path.relative_to(root).as_posix()
        if not path.is_file():
            fail('MISSING_REFERENCE', source, target=target)
            return None
        if rel in historical:
            fail('HISTORICAL_REFERENCE', source, target=target)
        elif path.suffix.lower() == '.md':
            body = path.read_text(encoding='utf-8')
            if inactive(body):
                fail('INACTIVE_SOURCE', rel)
            if fragment and fragment.lower() not in anchors(body):
                fail('MISSING_ANCHOR', source, target=target)
        elif fragment:
            fail('UNSUPPORTED_ANCHOR', source, target=target)
        snapshot[rel] = digest(path)
        return path

    for row in owners:
        target = link_target(row['Source'])
        path = validate(root, target, 'CODEX_START_HERE.md')
        if path:
            registered.add(path.relative_to(root).as_posix())
    for rel, expected in historical.items():
        try:
            path, fragment = local_target(root, root, rel)
            if fragment or not re.fullmatch(r'[0-9a-f]{64}', expected):
                raise ValueError('Invalid historical identity')
            if not path.is_file() or digest(path) != expected:
                fail('HISTORY_CHANGED', rel)
        except ValueError as exc:
            fail(str(exc), rel)
    actual = set()
    for path in root.rglob('*'):
        if path.is_symlink():
            fail('SYMLINK', path.relative_to(root))
        elif path.is_file() and path.suffix.lower() == '.md':
            actual.add(path.relative_to(root).as_posix())
    for rel in sorted(actual - registered - historical.keys() - {'CODEX_START_HERE.md'}):
        fail('UNINDEXED', rel)
    for rel in sorted(registered & historical.keys()):
        fail('CURRENT_HISTORY_OVERLAP', rel)
    for rel in sorted(registered | {'CODEX_START_HERE.md'}):
        path = root / rel
        if path.suffix.lower() != '.md':
            continue
        body = without_code(path.read_text(encoding='utf-8'))
        for match in re.finditer(r'(?<!!)\[[^\]\n]*\]\(([^\n)]+)\)', body):
            target = match.group(1).strip().strip('<>')
            url = urlsplit(target)
            if not url.scheme and not url.netloc:
                validate(path if not url.path else path.parent, target, rel)
        for match in re.finditer(r'`([^`\n<>]+\.md(?:#[^`\n]+)?)`', body):
            target = match.group(1)
            if (root / target.split('#')[0]).is_file():
                validate(root, target, rel)
    topics = {row['Topic'] for row in owners}
    for row in rows:
        if 'Dependency' not in row:
            continue
        if row['Topic'] not in topics:
            fail('UNKNOWN_DEPENDENCY_TOPIC', topic=row['Topic'])
        try:
            path, fragment = local_target(root, root, row['Dependency'])
            if fragment or not re.fullmatch(r'[0-9a-f]{64}', row['Reviewed SHA256']):
                raise ValueError('Invalid dependency identity')
            if not path.is_file() or digest(path) != row['Reviewed SHA256']:
                fail('DEPENDENCY_CHANGED', row['Dependency'], topic=row['Topic'])
            if path.is_file():
                snapshot[path.relative_to(root).as_posix()] = digest(path)
        except ValueError as exc:
            fail(str(exc), row['Dependency'])
    return {'mechanical_status': 'FAIL' if findings else 'PASS', 'semantic_status': 'UNKNOWN',
            'findings': findings, 'scope': str(root), 'documents': len(actual),
            'snapshot': snapshot, 'checker_sha256': digest(Path(__file__))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['check', 'hook'])
    parser.add_argument('--root', required=True)
    parser.add_argument('--event-log')
    args = parser.parse_args()
    root = Path(args.root).resolve()
    payload = None
    try:
        if args.command == 'hook':
            raw = sys.stdin.read(1000001)
            if len(raw) > 1000000:
                raise ValueError('Hook input exceeds pilot size limit')
            received = json.loads(raw)
            if not isinstance(received, dict):
                raise ValueError('Hook payload must be an object')
            event = received.get('hook_event_name')
            cwd = received.get('cwd')
            if not isinstance(event, str) or event not in {'SessionStart', 'PreToolUse', 'PostToolUse', 'Stop'}:
                raise ValueError('Unsupported hook event')
            if not isinstance(cwd, str) or not Path(cwd).is_absolute():
                raise ValueError('Hook cwd must be an absolute path')
            if not Path(cwd).resolve().is_relative_to(root):
                raise ValueError('Hook cwd is outside pilot root')
            if event == 'PreToolUse':
                tool_input = received.get('tool_input')
                if not isinstance(tool_input, dict) or not isinstance(tool_input.get('command', ''), str):
                    raise ValueError('Invalid tool input')
            payload = received
        result = check(root)
    except (OSError, ValueError) as exc:
        result = {'mechanical_status': 'ERROR', 'semantic_status': 'UNKNOWN',
                  'findings': [{'code': 'CHECK_ERROR', 'detail': str(exc)}]}
    if args.command == 'hook':
        event = payload.get('hook_event_name', 'Stop') if isinstance(payload, dict) else 'Stop'
        if args.event_log:
            try:
                with Path(args.event_log).open('a', encoding='utf-8') as stream:
                    stream.write(json.dumps({'event': event, 'time': time.time(), 'pid': os.getpid(),
                                             'session_id': (payload or {}).get('session_id'), 'root': str(root),
                                             'mechanical_status': result['mechanical_status'],
                                             'codes': [f['code'] for f in result['findings']]}) + '\n')
            except OSError as exc:
                result = {'mechanical_status': 'ERROR', 'findings': [{'code': 'LOG_ERROR', 'detail': str(exc)}]}
        summary = result['mechanical_status'] + ': ' + ', '.join(f['code'] + ':' + f.get('path', '') for f in result['findings'][:12])
        reply = hook_reply(event, payload or {}, root, result, summary)
        print(json.dumps(reply, ensure_ascii=False))
        return 0
    print(json.dumps(result, ensure_ascii=False))
    return {'PASS': 0, 'FAIL': 1, 'ERROR': 2}[result['mechanical_status']]


def hook_reply(event, payload, root, result, summary):
    if event == 'SessionStart':
        return {'hookSpecificOutput': {'hookEventName': event, 'additionalContext':
                f'Read {root / "CODEX_START_HERE.md"} then its task topic before editing. Mechanical {summary}; semantic validity UNKNOWN.'}}
    if event == 'PreToolUse':
        denied = result['mechanical_status'] == 'ERROR'
        tool_input = payload.get('tool_input', {})
        if payload.get('tool_name') == 'apply_patch' and isinstance(tool_input, dict):
            touched = []
            for match in re.finditer(r'^\*\*\* (?:Update File|Delete File|Add File|Move to): (.+)$', tool_input.get('command', ''), re.M):
                path = Path(match.group(1))
                touched.append((path if path.is_absolute() else Path(payload['cwd']) / path).resolve())
            if denied and touched and all(path == root / 'CODEX_START_HERE.md' for path in touched):
                return {'hookSpecificOutput': {'hookEventName': event, 'additionalContext':
                        'Index-only repair allowed; governance remains ERROR until PostToolUse recheck.'}}
            try:
                index_rows = list(tables((root / 'CODEX_START_HERE.md').read_text(encoding='utf-8')))
                protected = {(root / row['Historical file']).resolve().relative_to(root).as_posix()
                             for row in index_rows if 'Historical file' in row}
                for path in touched:
                    if path.is_relative_to(root) and path.relative_to(root).as_posix() in protected:
                        denied = True
            except (OSError, ValueError):
                denied = True
        if denied:
            return {'hookSpecificOutput': {'hookEventName': event, 'permissionDecision': 'deny',
                    'permissionDecisionReason': 'Protected historical evidence or checker unavailable. ' + summary}}
        return {'hookSpecificOutput': {'hookEventName': event, 'additionalContext':
                'History protection covers recognized apply_patch paths. Shell side effects require PostToolUse recheck.'}}
    if result['mechanical_status'] == 'PASS':
        return {'systemMessage': 'Document structure PASS; semantic validity remains UNKNOWN.'}
    if event == 'Stop' and payload.get('stop_hook_active'):
        return {'continue': False, 'stopReason': 'Document governance incomplete: ' + summary,
                'systemMessage': 'Repair budget reached; report incomplete. ' + summary}
    return {'decision': 'block', 'reason': 'Document governance incomplete; repair indexed corpus or report unresolved findings. ' + summary}


if __name__ == '__main__':
    raise SystemExit(main())
