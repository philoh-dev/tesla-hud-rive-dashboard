#!/usr/bin/env python3
"""Compare universal initial/live selection against dedicated vehicle renders."""
import json
import argparse
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops
from generate import ROOT, VEHICLES, IDS, Scene
from universal import (UniversalScene, VEHICLE_PROPERTY, VEHICLE_PROPERTY_ID,
                       FALLBACK_VEHICLE)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview-only',action='store_true',help='Render clean Park previews without the full regression suite.')
    args=parser.parse_args()
    output=ROOT/'build/universal-validation'
    output.mkdir(parents=True,exist_ok=True)
    local=ROOT/'.tooling'/('rive.exe' if os.name=='nt' else 'rive')
    cli=os.environ.get('RIVE_CLI') or (str(local) if local.exists() else shutil.which('rive'))
    if not cli:
        raise SystemExit('Install Rive CLI or set RIVE_CLI.')
    # Keep fixture controls separate as the vehicle catalogue grows.
    unknown_x,empty_x,park_x,drive_x=(20*(len(VEHICLES)+i) for i in range(1,5))

    def project(scene,name,controls=False,ground=True):
        path=output/name
        path.mkdir(exist_ok=True)
        document=scene.build()
        if not ground:
            parent=document.find(".//Node[@name='Native 800 pixel scene']")
            parent.remove(parent.find("Node[@name='Park ground']"))
        for asset in (*document.iter('ImageAsset'),*document.iter('FontAsset')):
            asset.set('file',str(ROOT/asset.get('file')))
        instance=document.find('ViewModel/ViewModelInstance')
        for key,value in dict(egoSpeed=0,leftBlinker=0,rightBlinker=0,leftBlindSpot=0,rightBlindSpot=0).items():
            next(n for n in instance if n.get('viewModelPropertyId')==IDS[key]).set('propertyValue',str(value))
        if controls:
            board=document.find("Artboard[@name='Newhaven']")
            machine=board.find('StateMachine')
            choices=[(20*(i+1),vehicle,VEHICLE_PROPERTY_ID,'String',635) for i,vehicle in enumerate(VEHICLES)]
            choices += [(unknown_x,'unknown-vehicle',VEHICLE_PROPERTY_ID,'String',635),
                        (empty_x,'',VEHICLE_PROPERTY_ID,'String',635),
                        (park_x,1,IDS['gear'],'Number',636),(drive_x,4,IDS['gear'],'Number',636)]
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
    # Pixel-exact comparison against the same shared floor in dedicated files.
    references={vehicle:project(Scene(vehicle),'reference-'+vehicle) for vehicle in VEHICLES}
    baseline=project(Scene(FALLBACK_VEHICLE),'reference-no-ground',ground=False)

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

    preview=project(UniversalScene(),'preview')
    for dark in (True,False):
        capture(preview,'park-preview-'+('dark' if dark else 'light'),1,FALLBACK_VEHICLE,dark=dark)
    if args.preview_only:
        print(f'Park previews rendered in {output}')
        return

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
                     events=(choose(vehicle),'--advance=3',f'--pointer=click@{park_x},20','--advance=3'))
    assert_same(actual,reference_images[(vehicle,1)],'selected model followed by Park')
    actual,_=capture(universal,'live-park-selection-then-drive',gear=1,selected=FALLBACK_VEHICLE,
                     events=(choose(vehicle),'--advance=3',f'--pointer=click@{drive_x},20','--advance=3'))
    assert_same(actual,reference_images[(vehicle,4)],'hidden Drive view follows selection in Park')
    for x,label in ((unknown_x,'unknown'),(empty_x,'empty')):
        actual,_=capture(universal,'live-fallback-'+label,selected=vehicle,
                         events=(f'--pointer=click@{x},20','--advance=3'))
        assert_same(actual,reference_images[(FALLBACK_VEHICLE,4)],'live '+label)
    for vehicle in (FALLBACK_VEHICLE,'model-3-highland-ultra-red','model-y-legacy-pearl-white-multi-coat'):
        for gear in (1,4):
            expected,_=capture(references[vehicle],f'light-reference-{vehicle}-{gear}',gear,dark=False)
            actual,_=capture(universal,f'light-{vehicle}-{gear}',gear,vehicle,dark=False)
            assert_same(actual,expected,f'light {vehicle} {gear}')
    for dark in (True,False):
        label='dark' if dark else 'light'
        original,_=capture(baseline,'no-ground-'+label,1,dark=dark)
        grounded,_=capture(universal,'park-ground-'+label,1,FALLBACK_VEHICLE,dark=dark)
        diff=ImageChops.difference(original.crop((0,40,1800,1080)),
                                   grounded.crop((0,40,1800,1080)))
        bounds=diff.getbbox()
        assert bounds is not None,f'{label}: Park ground must be visible'
        assert bounds[0]>250 and bounds[1]>360 and bounds[2]<1550 and bounds[3]<940,(
            f'{label}: ground changed pixels outside the local floor: {bounds}')
        for gear in (2,3,4):
            original,_=capture(baseline,f'no-ground-{label}-{gear}',gear,dark=dark)
            actual,_=capture(universal,f'ground-hidden-{label}-{gear}',gear,FALLBACK_VEHICLE,dark=dark)
            assert_same(actual,original,f'{label} ground hidden in gear {gear}')
        actual,_=capture(universal,'ground-hidden-after-park-'+label,1,FALLBACK_VEHICLE,dark=dark,
                         events=(f'--pointer=click@{drive_x},20','--advance=4'))
        original,_=capture(baseline,'drive-after-park-'+label,4,dark=dark)
        assert_same(actual,original,f'{label} ground disappears after shifting out of Park')
    print(f'Universal renderer checks passed: all {len(VEHICLES)} initial/live selections, Park/Drive switching,')
    print('generic fallbacks, light-theme comparisons and theme-aware, Park-only local ground shadows.')


if __name__=='__main__':
    main()
