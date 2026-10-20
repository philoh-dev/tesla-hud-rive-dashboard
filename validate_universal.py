#!/usr/bin/env python3
"""Compare universal initial/live selection against dedicated vehicle renders."""
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops
from generate import ROOT, VEHICLES, IDS, Scene
from universal import UniversalScene, VEHICLE_PROPERTY, VEHICLE_PROPERTY_ID, FALLBACK_VEHICLE


def main():
    output=ROOT/'build/universal-validation'
    output.mkdir(parents=True,exist_ok=True)
    local=ROOT/'.tooling'/('rive.exe' if os.name=='nt' else 'rive')
    cli=os.environ.get('RIVE_CLI') or (str(local) if local.exists() else shutil.which('rive'))
    if not cli:
        raise SystemExit('Install Rive CLI or set RIVE_CLI.')

    def project(scene,name,controls=False):
        path=output/name
        path.mkdir(exist_ok=True)
        document=scene.build()
        for asset in (*document.iter('ImageAsset'),*document.iter('FontAsset')):
            asset.set('file',str(ROOT/asset.get('file')))
        instance=document.find('ViewModel/ViewModelInstance')
        for key,value in dict(egoSpeed=0,leftBlinker=0,rightBlinker=0,leftBlindSpot=0,rightBlindSpot=0).items():
            next(n for n in instance if n.get('viewModelPropertyId')==IDS[key]).set('propertyValue',str(value))
        if controls:
            board=document.find("Artboard[@name='Newhaven']")
            machine=board.find('StateMachine')
            choices=[(20*(i+1),vehicle,VEHICLE_PROPERTY_ID,'String',635) for i,vehicle in enumerate(VEHICLES)]
            choices += [(300,'unknown-vehicle',VEHICLE_PROPERTY_ID,'String',635),
                        (320,'',VEHICLE_PROPERTY_ID,'String',635),
                        (340,1,IDS['gear'],'Number',636),(360,4,IDS['gear'],'Number',636)]
            for x,value,identity,kind,key in choices:
                scene.rect(board,'Universal test control',x,20,16,16,'FF000000')
                listener=scene.el(machine,'StateMachineListenerSingle',targetId=board[-1].get('id'),listenerTypeValue='click')
                prop=scene.el(scene.el(listener,'ListenerViewModelChange'),'BindableProperty'+kind,propertyValue=value)
                scene.el(prop,'DataBindContext',sourcePathIds=f'1:1-{identity}',propertyKey=key,direction=True)
        ET.indent(document,space='  ')
        ET.ElementTree(document).write(path/'scene.rml',encoding='unicode')
        (path/'rive.yaml').write_text('name: universal_validation\nmain: Newhaven\n')
        return path

    universal=project(UniversalScene(),'universal',True)
    references={vehicle:project(Scene(vehicle),'reference-'+vehicle) for vehicle in VEHICLES}

    def capture(path,name,gear=4,selected=None,dark=True,events=()):
        screenshot,dump=output/(name+'.png'),output/(name+'.json')
        args=[cli,str(path),f'--screenshot={screenshot}',f'--data-dump={dump}',
              '--viewport=1800x1080','--fit=layout',f'--data=gear={gear}',
              f'--data=darkMode={str(dark).lower()}']
        if selected is not None:
            args.append(f'--data={VEHICLE_PROPERTY}={selected}')
        result=subprocess.run([*args,'--advance=4',*events],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if result.returncode:
            raise RuntimeError(result.stdout)
        values={p['name']:p['value'] for p in json.loads(dump.read_text())['viewModel']['properties']}
        return Image.open(screenshot).convert('RGB'),values

    def assert_same(actual,expected,label):
        # Exclude the fixture-only controls at the very top, not dashboard UI.
        diff=ImageChops.difference(actual.crop((0,40,1800,1080)),expected.crop((0,40,1800,1080)))
        assert diff.getbbox() is None,f'{label}: universal differs from dedicated vehicle at {diff.getbbox()}'

    reference_images={}
    for vehicle in VEHICLES:
        for gear in (1,4):
            key=(vehicle,gear)
            expected,_=capture(references[vehicle],f'reference-{vehicle}-{gear}',gear)
            reference_images[key]=expected
            actual,values=capture(universal,f'initial-{vehicle}-{gear}',gear,vehicle)
            assert values[VEHICLE_PROPERTY]==vehicle
            assert_same(actual,expected,f'{vehicle} gear {gear}')
        print(f'Initial Park/Drive selection matches: {vehicle}',flush=True)

    for gear in (1,4):
        for index,value in enumerate((None,'','unknown-vehicle','MODEL-Y-JUNIPER-STEALTH-GREY')):
            actual,_=capture(universal,f'fallback-{gear}-{index}',gear,value)
            assert_same(actual,reference_images[(FALLBACK_VEHICLE,gear)],f'fallback {value!r}')

    def choose(vehicle):
        return f'--pointer=click@{20*(VEHICLES.index(vehicle)+1)},20'

    # Exercise every model after loading: not just authored initial values.
    for vehicle in VEHICLES:
        actual,values=capture(universal,'live-'+vehicle,selected=FALLBACK_VEHICLE,
                              events=(choose(vehicle),'--advance=3'))
        assert values[VEHICLE_PROPERTY]==vehicle
        assert_same(actual,reference_images[(vehicle,4)],f'live {vehicle}')
    vehicle='model-y-legacy-deep-blue-metallic'
    actual,_=capture(universal,'live-selection-then-park',selected=FALLBACK_VEHICLE,
                     events=(choose(vehicle),'--advance=3','--pointer=click@340,20','--advance=3'))
    assert_same(actual,reference_images[(vehicle,1)],'selected model followed by Park')
    actual,_=capture(universal,'live-park-selection-then-drive',gear=1,selected=FALLBACK_VEHICLE,
                     events=(choose(vehicle),'--advance=3','--pointer=click@360,20','--advance=3'))
    assert_same(actual,reference_images[(vehicle,4)],'hidden Drive view follows selection in Park')
    for x,label in ((300,'unknown'),(320,'empty')):
        actual,_=capture(universal,'live-fallback-'+label,selected=vehicle,
                         events=(f'--pointer=click@{x},20','--advance=3'))
        assert_same(actual,reference_images[(FALLBACK_VEHICLE,4)],'live '+label)
    for vehicle in (FALLBACK_VEHICLE,'model-3-highland-ultra-red'):
        for gear in (1,4):
            expected,_=capture(references[vehicle],f'light-reference-{vehicle}-{gear}',gear,dark=False)
            actual,_=capture(universal,f'light-{vehicle}-{gear}',gear,vehicle,dark=False)
            assert_same(actual,expected,f'light {vehicle} {gear}')
    print(f'Universal renderer checks passed: all {len(VEHICLES)} initial/live selections, Park/Drive switching,')
    print('generic default/empty/unknown fallbacks and representative light-theme comparisons.')


if __name__=='__main__':
    main()
