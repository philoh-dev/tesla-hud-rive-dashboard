#!/usr/bin/env python3
"""Verify immediate Park/Drive switching in the actual Rive renderer.

Requires Pillow and a graphics context. Click controls exist only in build/.
"""
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops
from generate import ROOT, Scene

OUTPUT=ROOT/'build'/'state-validation'


def fixture():
    scene=Scene()
    document=scene.build()
    for asset in (*document.iter('ImageAsset'),*document.iter('FontAsset')):
        asset.set('file',(ROOT/asset.get('file')).as_posix())
    main=document.find("Artboard[@name='Newhaven']")
    machine=main.find('StateMachine')
    for name,x,value in (('Park',20,1),('Drive',40,4),('Reverse',80,2),('Neutral',100,3)):
        target=scene.rect(main,name,x,20,16,16,'FF000000')
        # Listen on the Shape, not its Rectangle path.
        target=main[-1]
        listener=scene.el(machine,'StateMachineListenerSingle',name=name,
                          targetId=target.get('id'),listenerTypeValue='click')
        change=scene.el(listener,'ListenerViewModelChange')
        prop=scene.el(change,'BindablePropertyNumber',propertyValue=value)
        scene.bind(prop,'gear',636).set('direction','true')
    OUTPUT.mkdir(parents=True,exist_ok=True)
    ET.indent(document,space='  ')
    ET.ElementTree(document).write(OUTPUT/'scene.rml',encoding='unicode')
    (OUTPUT/'rive.yaml').write_text('name: state_validation\nmain: Newhaven\n')


def main():
    fixture()
    local=ROOT/'.tooling'/('rive.exe' if os.name=='nt' else 'rive')
    cli=os.environ.get('RIVE_CLI') or (str(local) if local.exists() else shutil.which('rive'))
    if not cli:
        raise SystemExit('Install Rive CLI 1.6.0 or set RIVE_CLI.')

    def capture(name,gear,*events):
        image=OUTPUT/(name+'.png')
        dump=OUTPUT/(name+'.json')
        command=[cli,str(OUTPUT),'--viewport=1800x1080',f'--data=gear={gear}',
                 '--data=egoSpeed=0','--data=powerLevel=0','--data=adasOn=false',
                 '--data=leftBlinker=0','--data=rightBlinker=0',
                 '--data=leftBlindSpot=0','--data=rightBlindSpot=0',
                 f'--screenshot={image}',f'--data-dump={dump}',*events]
        result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if result.returncode:
            raise RuntimeError(result.stdout)
        values={p['name']:p['value'] for p in json.loads(dump.read_text())['viewModel']['properties']}
        return Image.open(image).convert('RGB'),values

    def same(a,b):
        return ImageChops.difference(a,b).getbbox() is None

    parked,_=capture('park',1,'--advance=3')
    driving,_=capture('drive',4,'--advance=3')
    for name,initial,button,expected,gear in (
        ('park-to-drive',1,40,driving,4),('drive-to-park',4,20,parked,1)):
        result,values=capture(name,initial,'--advance=3',f'--pointer=click@{button},20','--advance=1')
        assert values['gear']==gear, 'Fixture did not update gear'
        assert same(result,expected), f'{name} did not switch to its static view immediately'
    result,_=capture('rapid-return',1,'--advance=3','--pointer=click@40,20',
                     '--advance=1','--pointer=click@20,20','--advance=1')
    assert same(result,parked), 'Rapid return left an intermediate pose'
    # Compare the ego car only: stopped D/R intentionally show different
    # direction cues, while N has no arrow at all.
    crop=(790,465,1010,690)
    for gear,button in ((2,80),(3,100)):
        result,values=capture(f'gear-{gear}',1,'--advance=3',f'--pointer=click@{button},20','--advance=1')
        assert values['gear']==gear
        assert same(result.crop(crop),driving.crop(crop)), 'R/N do not share the Drive view'
    result,_=capture('park-hides-instruments',1,'--data=egoSpeed=130',
                     '--data=powerLevel=70','--advance=3')
    blank=Image.new('RGB',(400,720),(0,0,0))
    assert same(result.crop((0,60,400,780)),blank), 'Park instruments remain visible'
    road_blank=Image.new('RGB',(300,160),(0,0,0))
    assert same(parked.crop((750,0,1050,160)),road_blank), 'Road remains visible in Park'
    assert not same(driving.crop((750,0,1050,160)),road_blank), 'Road is missing in Drive'
    print('Runtime checks passed: immediate gear views, R/N, rapid return and hidden Park instruments/road.')


if __name__=='__main__':
    main()
