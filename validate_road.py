#!/usr/bin/env python3
"""Check actual Rive road movement using synchronized initial telemetry.

Seed units and speed together before load. Sequential CLI --data writes can
legitimately accumulate a different starting phase while values are updating.
"""
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops, ImageStat
from generate import ROOT, Scene, IDS


def main():
    output=ROOT/'build'/'road-validation'
    output.mkdir(parents=True,exist_ok=True)
    local=ROOT/'.tooling'/('rive.exe' if os.name=='nt' else 'rive')
    cli=os.environ.get('RIVE_CLI') or (str(local) if local.exists() else shutil.which('rive'))
    if not cli:
        raise SystemExit('Install Rive CLI or set RIVE_CLI.')

    def capture(name,speed,frames,gear=4,imperial=False):
        path=output/(name+'.png')
        fixture=output/name
        fixture.mkdir(exist_ok=True)
        document=Scene().build()
        for asset in (*document.iter('ImageAsset'),*document.iter('FontAsset')):
            asset.set('file',str(ROOT/asset.get('file')))
        instance=document.find('ViewModel/ViewModelInstance')
        values=dict(egoSpeed=speed,gear=gear,isImperial=imperial,adasOn=False,
                    leftBlinker=0,rightBlinker=0,leftBlindSpot=0,rightBlindSpot=0)
        for prop,value in values.items():
            node=next(n for n in instance if n.get('viewModelPropertyId')==IDS[prop])
            node.set('propertyValue',str(value).lower())
        ET.indent(document,space='  ')
        ET.ElementTree(document).write(fixture/'scene.rml',encoding='unicode')
        (fixture/'rive.yaml').write_text('name: road_validation\nmain: Newhaven\n')
        result=subprocess.run([cli,str(fixture),f'--screenshot={path}','--viewport=1800x1080',
            f'--advance={frames}'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if result.returncode:
            raise RuntimeError(result.stdout)
        # Isolate one lane boundary; the center now contains the stopped arrow.
        return Image.open(path).convert('RGB').crop((700,0,825,350))

    def error(a,b):
        return sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3

    stopped=capture('stopped-start',0,1)
    assert error(stopped,capture('stopped-later',0,30))==0, 'Road moves at zero speed'
    early=capture('moving-early',43.2,15)
    later=capture('moving-later',43.2,30)
    assert error(early,later)>1, 'Road does not animate'
    assert error(later,capture('double-speed-half-time',86.4,15))<.2, 'Motion is not proportional to speed'
    assert error(later,capture('mph',43.2/1.609344,30,imperial=True))<.2, 'mph physical distance differs'
    assert error(stopped,capture('neutral',100,30,gear=3))<.2, 'Neutral advances the road'
    print('Actual Rive road checks passed: zero speed, motion, proportional speed, mph and Neutral.')


if __name__=='__main__':
    main()
