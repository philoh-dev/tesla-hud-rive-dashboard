#!/usr/bin/env python3
"""Generate, verify and compile the isolated Newhaven Rive project."""
import os
import argparse
from pathlib import Path
import shutil
import subprocess

from generate import ROOT, generate, VEHICLES, DEFAULT_VEHICLE

OUTPUT = ROOT / 'dashboard' / 'model-y-juniper-stealth-grey.riv'


def main():
    parser = argparse.ArgumentParser(description='Build all vehicle dashboards or one selected design.')
    parser.add_argument('--vehicle', choices=VEHICLES)
    args = parser.parse_args()
    local = ROOT / '.tooling' / ('rive.exe' if os.name == 'nt' else 'rive')
    cli = os.environ.get('RIVE_CLI') or (str(local) if local.exists() else shutil.which('rive'))
    if not cli:
        raise SystemExit('Install Rive CLI 1.6.0 or set RIVE_CLI to its executable.')
    try:
        for vehicle in (args.vehicle,) if args.vehicle else VEHICLES:
            generate(vehicle)
            subprocess.run([cli, str(ROOT), '--verify'], check=True)
            subprocess.run([cli, str(ROOT), '--once'], check=True)
            result = ROOT / 'build' / 'thud_dashboard.riv'
            if result.stat().st_size > 5_000_000:
                raise SystemExit(f'{vehicle} dashboard exceeds the contest 5 MB limit.')
            output = ROOT / 'dashboard' / f'{vehicle}.riv'
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(result, output)
            print(f'{output}: {output.stat().st_size:,} bytes')
    finally:
        # scene.rml is the canonical default design, regardless of build order.
        generate(DEFAULT_VEHICLE)


if __name__ == '__main__':
    main()
