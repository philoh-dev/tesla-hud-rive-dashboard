#!/usr/bin/env python3
"""Generate, verify and compile the isolated Newhaven Rive project."""
import os
from pathlib import Path
import shutil
import subprocess

from generate import ROOT, generate

OUTPUT = ROOT / 'dashboard' / 'model-y-juniper-stealth-grey.riv'


def main():
    local = ROOT / '.tooling' / ('rive.exe' if os.name == 'nt' else 'rive')
    cli = os.environ.get('RIVE_CLI') or (str(local) if local.exists() else shutil.which('rive'))
    if not cli:
        raise SystemExit('Install Rive CLI 1.6.0 or set RIVE_CLI to its executable.')
    generate()
    subprocess.run([cli, str(ROOT), '--verify'], check=True)
    subprocess.run([cli, str(ROOT), '--once'], check=True)
    result = ROOT / 'build' / 'thud_dashboard.riv'
    if result.stat().st_size > 5_000_000:
        raise SystemExit('Dashboard exceeds the contest 5 MB limit.')
    output = OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(result, output)
    print(f'{output}: {output.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
