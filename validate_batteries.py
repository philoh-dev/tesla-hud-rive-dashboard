#!/usr/bin/env python3
"""Actual-renderer checks for the independent car/phone footer widgets."""
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops
from generate import ROOT, Scene


def main():
    output=ROOT/'build'/'battery-validation'
    output.mkdir(parents=True,exist_ok=True)
    scene=Scene()
    document=scene.build()
    for asset in (*document.iter('ImageAsset'),*document.iter('FontAsset')):
        asset.set('file',str(ROOT/asset.get('file')))
    board=document.find("Artboard[@name='Newhaven']")
    machine=board.find('StateMachine')
    for x,name,value,kind,key in ((20,'showPhoneBattery',False,'Boolean',634),
                                (40,'showPhoneBattery',True,'Boolean',634),
                                (60,'phoneBattery',0,'Number',636),
                                (80,'phoneBattery',100,'Number',636),
                                (100,'phoneBattery',-1,'Number',636),
                                (120,'showOdometer',False,'Boolean',634),
                                (140,'showOdometer',True,'Boolean',634),
                                (160,'odometer',999,'Number',636),
                                (180,'odometer',1000,'Number',636),
                                (200,'odometer',1000005,'Number',636),
                                (220,'isImperial',True,'Boolean',634)):
        scene.rect(board,'Battery test control',x,20,16,16,'FF000000')
        listener=scene.el(machine,'StateMachineListenerSingle',targetId=board[-1].get('id'),listenerTypeValue='click')
        change=scene.el(listener,'ListenerViewModelChange')
        prop=scene.el(change,'BindableProperty'+kind,propertyValue=value)
        scene.bind(prop,name,key).set('direction','true')
    ET.indent(document,space='  ')
    ET.ElementTree(document).write(output/'scene.rml',encoding='unicode')
    (output/'rive.yaml').write_text('name: battery_validation\nmain: Newhaven\n')
    local=ROOT/'.tooling'/('rive.exe' if os.name=='nt' else 'rive')
    cli=os.environ.get('RIVE_CLI') or (str(local) if local.exists() else shutil.which('rive'))
    if not cli:
        raise SystemExit('Install Rive CLI or set RIVE_CLI.')

    def capture(name,dark,number=78,shown=True,*events,odometer=123456,is_imperial=False):
        path=output/f'{dark}-{name}.png'
        result=subprocess.run([cli,str(output),'--viewport=1440x1080','--fit=layout',
            f'--screenshot={path}',f'--data=darkMode={str(dark).lower()}',
            f'--data=showPhoneBattery={str(shown).lower()}',f'--data=phoneBattery={number}',
            f'--data=odometer={odometer}','--data=showOdometer=true',
            f'--data=isImperial={str(is_imperial).lower()}',
            '--data=adasOn=true','--data=gear=4','--advance=3',*events],
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if result.returncode:
            raise RuntimeError(result.stdout)
        return Image.open(path).convert('RGB')

    phone_box=(1040,900,1320,1080)
    car_box=(45,900,350,1080)
    odo_box=(324,930,640,1020)
    def same(a,b):
        return ImageChops.difference(a,b).getbbox() is None

    for dark in (True,False):
        normal=capture('normal',dark)
        hidden=capture('hidden',dark,78,False)
        blank=Image.new('RGB',(280,180),(0,0,0) if dark else (255,255,255))
        assert same(hidden.crop(phone_box),blank), 'Phone preference did not hide the whole widget'
        assert not same(normal.crop(phone_box),blank), 'Phone widget is missing'
        assert same(normal.crop(car_box),hidden.crop(car_box)), 'Phone setting changed the car widget'
        for number in (0,100,-1):
            expected=capture(f'value-{number}',dark,number)
            button={0:60,100:80,-1:100}[number]
            live=capture(f'live-{number}',dark,78,True,f'--pointer=click@{button},20','--advance=2')
            assert same(expected.crop(phone_box),live.crop(phone_box)), 'Live phone value did not redraw'
            assert same(expected.crop(phone_box),blank)==(number<0), 'Zero or unknown battery handled incorrectly'
        live=capture('hide-show',dark,78,True,'--pointer=click@20,20','--advance=1',
                     '--pointer=click@40,20','--advance=2')
        assert same(normal.crop(phone_box),live.crop(phone_box)), 'Phone preference did not restore the widget'
        odo_blank=Image.new('RGB',(316,90),(0,0,0) if dark else (255,255,255))
        hidden=capture('odometer-hidden',dark,78,True,'--pointer=click@120,20','--advance=2')
        assert same(hidden.crop(odo_box),odo_blank), 'Odometer preference did not hide value and unit'
        live=capture('odometer-restored',dark,78,True,'--pointer=click@120,20','--advance=1',
                     '--pointer=click@140,20','--advance=2')
        assert same(live.crop(odo_box),normal.crop(odo_box)), 'Odometer preference did not restore the reading'
        for number,button in ((999,160),(1000,180),(1000005,200)):
            expected=capture(f'odometer-{number}',dark,odometer=number)
            live=capture(f'odometer-live-{number}',dark,78,True,
                         f'--pointer=click@{button},20','--advance=2')
            assert same(expected.crop(odo_box),live.crop(odo_box)), 'Live odometer grouping did not update'
        negative=capture('odometer-unknown',dark,odometer=-1)
        assert same(negative.crop(odo_box),odo_blank), 'Unknown odometer remains visible'
        metric=capture('odometer-1609km',dark,odometer=1609)
        imperial=capture('odometer-1000mi',dark,odometer=1000,is_imperial=True)
        assert same(metric.crop(odo_box),imperial.crop(odo_box)), 'Imperial odometer was mislabeled as km'
        live=capture('odometer-live-imperial',dark,78,True,'--pointer=click@220,20','--advance=2',odometer=1000)
        assert same(live.crop(odo_box),imperial.crop(odo_box)), 'Live odometer unit conversion failed'
        muted=(124,133,137) if dark else (139,147,150)
        assert sum(n for n,color in normal.crop(odo_box).getcolors(1_000_000) if color==muted)>20, \
            'Odometer km suffix is not muted'
    print('Battery renderer checks passed: both themes, 0/78/100/unknown, live updates and independent visibility.')
    print('Odometer checks passed: live thousand/million boundaries, visibility, muted suffix and imperial-to-km conversion.')


if __name__=='__main__':
    main()
