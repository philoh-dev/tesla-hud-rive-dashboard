#!/usr/bin/env python3
"""Compare actual Rive edge/center anchors at DashPilot landscape widths."""
import os
import shutil
import subprocess

from PIL import Image, ImageChops, ImageStat
from generate import ROOT


def main():
    output=ROOT/'build'/'layout-validation'
    output.mkdir(parents=True,exist_ok=True)
    local=ROOT/'.tooling'/('rive.exe' if os.name=='nt' else 'rive')
    cli=os.environ.get('RIVE_CLI') or (str(local) if local.exists() else shutil.which('rive'))
    if not cli:
        raise SystemExit('Install Rive CLI or set RIVE_CLI.')

    def capture(width,gear):
        path=output/f'{width}-gear-{gear}.png'
        result=subprocess.run([cli,str(ROOT),f'--screenshot={path}',
            f'--viewport={width}x1080','--fit=layout',f'--data=gear={gear}',
            '--data=egoSpeed=0','--data=powerLevel=35','--data=adasOn=true',
            '--data=leftBlinker=0','--data=rightBlinker=0','--advance=1'],
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if result.returncode:
            raise RuntimeError(result.stdout)
        return Image.open(path).convert('RGB')

    def parts(image):
        width=image.width
        return {
            'speed':image.crop((0,90,450,330)),
            'power rail':image.crop((0,330,75,800)),
            'car battery':image.crop((0,900,350,1080)),
            'odometer':image.crop((310,900,640,1080)),
            'phone battery':image.crop((width-400,900,width-120,1080)),
            'speed limit':image.crop((width-300,0,width,350)),
            'gear':image.crop((width-120,900,width,1080)),
            'road and vehicles':image.crop((width//2-620,400,width//2+620,850)),
            'upper road':image.crop((width//2-140,0,width//2+140,350)),
            'autopilot':image.crop((width//2-100,864,width//2+100,1080)),
        }

    for gear in (1,4):
        reference=parts(capture(1800,gear))
        for width in (1440,2340):
            rendered=parts(capture(width,gear))
            for name,expected in reference.items():
                # GPU text rasterization can vary by one channel value after
                # a viewport change; reject displacement, not that rounding.
                difference=ImageChops.difference(expected,rendered[name])
                assert max(ImageStat.Stat(difference).mean)<.02, \
                    f'{name} moved relative to its anchor at {width}px, gear {gear}'
    print('Actual Rive layout checks passed: left/right/center anchors at 1440, 1800 and 2340 x 1080 in Park and Drive.')


if __name__=='__main__':
    main()
