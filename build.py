#!/usr/bin/env python3
"""Generate, verify and compile the isolated Newhaven Rive project."""
import os
import argparse
from pathlib import Path
import shutil
import subprocess

from generate import ROOT, generate, VEHICLES, DEFAULT_VEHICLE
from universal import UNIVERSAL_TARGET, generate_universal
from optimize_export import prepare_export

OUTPUT = ROOT / 'dashboard' / 'model-y-juniper-stealth-grey.riv'


def main():
    parser = argparse.ArgumentParser(description='Build all vehicle dashboards or one selected design.')
    selection=parser.add_mutually_exclusive_group()
    selection.add_argument('--vehicle', choices=VEHICLES)
    selection.add_argument('--universal',action='store_true',help='Build only the live vehicle-selecting dashboard.')
    args = parser.parse_args()
    local = ROOT / '.tooling' / ('rive.exe' if os.name == 'nt' else 'rive')
    cli = os.environ.get('RIVE_CLI') or (str(local) if local.exists() else shutil.which('rive'))
    if not cli:
        raise SystemExit('Install Rive CLI 1.6.0 or set RIVE_CLI to its executable.')
    try:
        targets=(UNIVERSAL_TARGET,) if args.universal else (args.vehicle,) if args.vehicle else (*VEHICLES,UNIVERSAL_TARGET)
        for vehicle in targets:
            if vehicle==UNIVERSAL_TARGET:
                generate_universal()
            else:
                generate(vehicle)
            project = prepare_export()
            subprocess.run([cli, str(project), '--verify'], check=True)
            subprocess.run([cli, str(project), '--once'], check=True)
            result = project / 'build' / 'thud_dashboard.riv'
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
