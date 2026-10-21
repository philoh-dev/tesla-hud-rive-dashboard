#!/usr/bin/env python3
"""Native Rive checks for live, smoothed steering and speed-driven curved lanes.

Fixture controls exist only in ignored build/steering-validation, never exports.
"""
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops
from generate import ROOT, Scene, IDS, ROAD_BEND


def main():
    output=ROOT/'build'/'steering-validation'
    output.mkdir(parents=True,exist_ok=True)
    scene=Scene()
    document=scene.build()
    for asset in (*document.iter('ImageAsset'),*document.iter('FontAsset')):
        asset.set('file',(ROOT/asset.get('file')).as_posix())
    values=dict(egoSpeed=0,egoSteeringAngle=0,leftBlinker=0,rightBlinker=0,
                leftBlindSpot=0,rightBlindSpot=0)
    instance=document.find('ViewModel/ViewModelInstance')
    for name,value in values.items():
        next(n for n in instance if n.get('viewModelPropertyId')==IDS[name]).set('propertyValue',str(value))
    board=document.find("Artboard[@name='Newhaven']")
    machine=board.find('StateMachine')
    for x,angle in ((20,60),(40,-60),(60,0)):
        scene.rect(board,'Steering test control',x,20,16,16,'FF000000')
        listener=scene.el(machine,'StateMachineListenerSingle',targetId=board[-1].get('id'),listenerTypeValue='click')
        value=scene.el(scene.el(listener,'ListenerViewModelChange'),'BindablePropertyNumber',propertyValue=angle)
        scene.bind(value,'egoSteeringAngle',636).set('direction','true')
    ET.indent(document,space='  ')
    ET.ElementTree(document).write(output/'scene.rml',encoding='unicode')
    (output/'rive.yaml').write_text('name: steering_validation\nmain: Newhaven\n')
    local=ROOT/'.tooling'/('rive.exe' if os.name=='nt' else 'rive')
    cli=os.environ.get('RIVE_CLI') or (str(local) if local.exists() else shutil.which('rive'))
    if not cli:
        raise SystemExit('Install Rive CLI or set RIVE_CLI.')

    def capture(name,angle=0,speed=0,gear=4,dark=True,assist=True,frames=20,events=(),width=1800):
        path,dump=output/(name+'.png'),output/(name+'.json')
        result=subprocess.run([cli,str(output),f'--screenshot={path}',f'--data-dump={dump}',
            f'--viewport={width}x1080','--fit=layout',f'--data=egoSteeringAngle={angle}',
            f'--data=egoSpeed={speed}',f'--data=gear={gear}',f'--data=darkMode={str(dark).lower()}',
            f'--data=adasOn={str(assist).lower()}',f'--advance={frames}',*events],
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if result.returncode:
            raise RuntimeError(result.stdout)
        data={p['name']:p['value'] for p in json.loads(dump.read_text())['viewModel']['properties']}
        return Image.open(path).convert('RGB'),data

    def same(a,b,box):
        return ImageChops.difference(a.crop(box),b.crop(box)).getbbox() is None

    def lane_center(image,y):
        pixels=[x for x in range(620,1220) if (lambda c:c[2]>160 and c[0]<30 and c[1]<150)(image.getpixel((x,y)))]
        assert len(pixels)>2,f'No blue lane pixels at y={y}'
        return (min(pixels)+max(pixels))/2

    straight,_=capture('straight')
    right,right_data=capture('right',60)
    left,left_data=capture('left',-60)
    hard,_=capture('hard-right',90)
    clamped,_=capture('clamped-right',819)
    dead,_=capture('dead-zone',1.9)
    assert same(straight,dead,(600,0,1250,850)),'Tiny steering movements bend the road'
    assert same(hard,clamped,(600,0,1250,850)),'Full-lock steering is not bounded'
    centers=[lane_center(image,100) for image in (left,straight,right,hard)]
    assert centers==sorted(centers) and len(set(centers))==4,centers
    assert abs((centers[0]+centers[2])/2-centers[1])<1,'Left/right curve is not symmetric'
    # The existing lane-centering effect translates the road with steering;
    # the ego vehicle remains fixed. Isolate it from both lane boundaries.
    assert same(straight,right,(790,465,1010,690)),'Steering moved the ego car'
    assert same(straight,right,(0,900,1800,1080)),'Steering moved footer instruments'
    expected=eval(ROAD_BEND,{'__builtins__':{}},dict(input=60,min=min,max=max))
    assert abs(right_data['_roadBend']-expected)<1e-5
    assert abs(left_data['_roadBend']+expected)<1e-5

    # A real input update after load must interpolate, not merely start curved.
    response=[]
    for frames in (1,3,12):
        _,data=capture(f'live-right-{frames}',events=('--pointer=click@20,20',f'--advance={frames}'))
        assert data['egoSteeringAngle']==60,'Fixture did not change steering'
        response.append(data['_roadBend'])
    assert 0<response[0]<response[1]<response[2],response
    assert abs(response[-1]-expected)<1e-5,response
    restored,data=capture('live-reset',events=('--pointer=click@20,20','--advance=12',
                        '--pointer=click@60,20','--advance=12'))
    assert abs(data['_roadBend'])<1e-6
    assert same(straight,restored,(600,0,1250,850)),'Live steering reset does not return straight'
    flipped,data=capture('live-opposite',events=('--pointer=click@20,20','--advance=12',
                       '--pointer=click@40,20','--advance=12'))
    assert same(left,flipped,(600,0,1250,850)),'Live reversal does not reach the left curve'

    early,early_data=capture('moving-early',60,43.2,frames=15)
    later,later_data=capture('moving-later',60,43.2,frames=30)
    assert not same(early,later,(620,0,1220,850)),'Curved road does not move'
    assert early_data['_roadPhase']!=later_data['_roadPhase'],'Road phase did not advance'
    _,stopped_data=capture('stopped-later',60,frames=60)
    assert abs(stopped_data['_roadPhase'])<1e-6,'Road moves while stopped'
    for dark in (True,False):
        for assist in (True,False):
            before,_=capture(f'{dark}-{assist}-straight',dark=dark,assist=assist)
            curved,_=capture(f'{dark}-{assist}-right',60,dark=dark,assist=assist)
            assert not same(before,curved,(620,0,1220,350)),'Theme/assist lost the curve'
            assert same(before,curved,(790,465,1010,690)),'Theme/assist moved the ego car'
        parked,_=capture(f'park-{dark}',gear=1,dark=dark)
        parked_turned,_=capture(f'park-turned-{dark}',60,gear=1,dark=dark)
        assert same(parked,parked_turned,(100,0,1800,1080)),'Park shows steering effects'
    for width in (2340,2520):
        image,_=capture(f'phone-{width}',60,speed=80,width=width)
        assert image.size==(width,1080)
    print('Native steering checks passed: signed/bounded curve, dead zone, live interpolation/reset/reversal,')
    print('moving/stopped road, fixed near geometry and instruments, both themes/assist states, Park and phone widths.')
    print(f'Live 60-degree bend after 1/3/12 frames: {response}')


if __name__=='__main__':
    main()
