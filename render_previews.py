#!/usr/bin/env python3
"""Capture current README images from the real Rive renderer, not mockups."""
import os
import argparse
import shutil
import subprocess

from generate import ROOT, generate, VEHICLES, DEFAULT_VEHICLE

PREVIEWS=(
    ('drive-dark',dict(gear=4,egoSpeed=130,fusedSpeedLimit=130,powerLevel=35,
                       darkMode=True,adasOn=True,accSetSpeed=130,odometer=123456,showOdometer=True,phoneBattery=78,showPhoneBattery=True,leftBlinker=2,rightBlinker=0,
                       leftBlindSpot=1,rightBlindSpot=1)),
    ('drive-light',dict(gear=4,egoSpeed=130,fusedSpeedLimit=130,powerLevel=35,
                        darkMode=False,adasOn=False,accSetSpeed=130,odometer=123456,showOdometer=True,phoneBattery=78,showPhoneBattery=True,leftBlinker=2,rightBlinker=0,
                        leftBlindSpot=1,rightBlindSpot=1)),
    ('park-dark',dict(gear=1,egoSpeed=0,fusedSpeedLimit=0,powerLevel=0,
                      darkMode=True,adasOn=False,odometer=123456,showOdometer=True,phoneBattery=78,showPhoneBattery=True,leftBlinker=0,rightBlinker=0,
                      leftBlindSpot=0,rightBlindSpot=0)),
)


def main():
    parser=argparse.ArgumentParser(description='Render all vehicle previews or one selected design.')
    parser.add_argument('--vehicle',choices=VEHICLES)
    args=parser.parse_args()
    local=ROOT/'.tooling'/('rive.exe' if os.name=='nt' else 'rive')
    cli=os.environ.get('RIVE_CLI') or (str(local) if local.exists() else shutil.which('rive'))
    if not cli:
        raise SystemExit('Install Rive CLI 1.6.0 or set RIVE_CLI.')
    try:
        for vehicle in (args.vehicle,) if args.vehicle else VEHICLES:
            generate(vehicle)
            output=ROOT/'docs'/'images'/vehicle
            output.mkdir(parents=True,exist_ok=True)
            for name,values in PREVIEWS:
                arguments=[f'--data={key}={str(value).lower()}' for key,value in values.items()]
                subprocess.run([cli,str(ROOT),f'--screenshot={output/(name+".png")}',
                                '--viewport=1800x1080',*arguments,'--advance=3'],check=True)
    finally:
        generate(DEFAULT_VEHICLE)


if __name__=='__main__':
    main()
