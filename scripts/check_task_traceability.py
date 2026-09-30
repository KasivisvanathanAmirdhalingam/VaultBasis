#!/usr/bin/env python3
"""Validate task identifiers and current implementation closeout, not product quality."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = {'technical', 'knowledge_base', 'status', 'adr', 'internal_audit', 'external_audit'}
CLOSED = {'IMPLEMENTED', 'AUTOMATED_VALIDATION_PASS', 'BUILD_VERIFIED',
          'PREPROD_DEPLOYED', 'PREPROD_QUALIFIED', 'DISTRIBUTION_QUALIFIED',
          'RELEASE_QUALIFIED', 'PRODUCTION_PROMOTED', 'PRODUCTION_VERIFIED',
          'PRACTITIONER_QUALIFIED'}
STATES = CLOSED | {'HISTORICAL_RECORDED', 'IN_PROGRESS', 'AUTHORIZED', 'PENDING',
                   'PLANNED', 'RESEARCH_LAB', 'DIRECTIONAL', 'BLOCKED', 'FAILED',
                   'REJECTED', 'SUPERSEDED', 'READY_FOR_FOUNDER_REVIEW', 'FOUNDER_UX_ACCEPTED'}


def validate(data):
    errors, seen = [], set()
    historical = 0
    for task in data.get('tasks', []):
        tid = task.get('id', '')
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9.-]*', tid) or tid in seen:
            errors.append(f'{tid}: missing/invalid/duplicate task ID')
        seen.add(tid)
        if task.get('state') not in STATES:
            errors.append(f'{tid}: unknown or ambiguous state')
        for field in ('title', 'stage', 'ledger', 'state', 'owner', 'acceptance'):
            if not task.get(field):
                errors.append(f'{tid}: missing {field}')
        for field in ('ledger',):
            if not (ROOT / task.get(field, '__missing__')).is_file():
                errors.append(f'{tid}: {field} file missing')
        commits = task.get('implementation_commits', [])
        if not isinstance(commits, list):
            errors.append(f'{tid}: implementation_commits must be a list')
            commits = []
        for sha in commits:
            if not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{40}', sha):
                errors.append(f'{tid}: commit must be a full SHA')
            elif subprocess.run(['git', 'cat-file', '-e', sha + '^{commit}'],
                                cwd=ROOT, capture_output=True).returncode:
                errors.append(f'{tid}: commit does not resolve: {sha}')
        if task.get('historical_import'):
            historical += 1
            if task.get('state') != 'HISTORICAL_RECORDED' or not task.get('historical_note'):
                errors.append(f'{tid}: historical exemption requires explicit historical state/note')
            continue
        if task.get('state') in CLOSED | {'READY_FOR_FOUNDER_REVIEW', 'FOUNDER_UX_ACCEPTED'}:
            if not commits:
                errors.append(f'{tid}: implementation-closed task has no commit')
            if not (ROOT / task.get('closeout', '__missing__')).is_file():
                errors.append(f'{tid}: missing closeout')
            dispositions = task.get('documentation', {})
            if set(dispositions) != CATEGORIES:
                errors.append(f'{tid}: all six documentation categories required')
            for name, item in dispositions.items():
                if item.get('disposition') not in ('UPDATED', 'NO_CHANGE') or not item.get('rationale', '').strip():
                    errors.append(f'{tid}: {name} requires disposition and rationale')
                paths = item.get('paths', [])
                if not paths or any(not (ROOT / p).is_file() for p in paths):
                    errors.append(f'{tid}: {name} requires existing linked document(s)')
    if not seen:
        errors.append('Registry contains no tasks')
    return errors, historical


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', type=Path, default=ROOT / 'docs/task_registry.json')
    args = parser.parse_args()
    try:
        data = json.loads(args.registry.read_text())
        errors, historical = validate(data)
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(f'Traceability input error: {exc}', file=sys.stderr)
        return 1
    for error in errors:
        print(error, file=sys.stderr)
    print(f'{len(data["tasks"])} task IDs checked; {historical} historical imports '
          f'(not requalified); {len(errors)} traceability errors.')
    return int(bool(errors))


if __name__ == '__main__':
    sys.exit(main())
