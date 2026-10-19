#!/usr/bin/env python3
"""Verify exact theme colors and live switching in actual Rive captures."""
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops, ImageStat
from generate import ROOT, Scene


def main():
    output=ROOT/'build'/'theme-validation'
    output.mkdir(parents=True,exist_ok=True)
    scene=Scene()
    document=scene.build()
    for asset in (*document.iter('ImageAsset'),*document.iter('FontAsset')):
        asset.set('file',str(ROOT/asset.get('file')))
    main_board=document.find("Artboard[@name='Newhaven']")
    machine=main_board.find('StateMachine')
    for x,value in ((20,True),(40,False)):
        scene.rect(main_board,'Theme test control',x,20,16,16,'FF000000')
        listener=scene.el(machine,'StateMachineListenerSingle',targetId=main_board[-1].get('id'),
                          listenerTypeValue='click',name='Set theme')
        change=scene.el(listener,'ListenerViewModelChange')
        prop=scene.el(change,'BindablePropertyBoolean',propertyValue=value)
        scene.bind(prop,'darkMode',634).set('direction','true')
    ET.indent(document,space='  ')
    ET.ElementTree(document).write(output/'scene.rml',encoding='unicode')
    (output/'rive.yaml').write_text('name: theme_validation\nmain: Newhaven\n')
    local=ROOT/'.tooling'/('rive.exe' if os.name=='nt' else 'rive')
    cli=os.environ.get('RIVE_CLI') or (str(local) if local.exists() else shutil.which('rive'))
    if not cli:
        raise SystemExit('Install Rive CLI or set RIVE_CLI.')

    def capture(name,dark,assist=False,*events):
        path=output/(name+'.png')
        result=subprocess.run([cli,str(output),f'--screenshot={path}','--viewport=1800x1080',
            f'--data=darkMode={str(dark).lower()}','--data=darkModeBackgroundGray=127',
            f'--data=adasOn={str(assist).lower()}','--data=gear=3','--data=egoSpeed=130',
            '--data=leftBlinker=0','--data=rightBlinker=0','--data=leftBlindSpot=0',
            '--data=rightBlindSpot=0','--advance=3',*events],
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if result.returncode:
            raise RuntimeError(result.stdout)
        return Image.open(path).convert('RGB')

    def contains(image,box,color):
        counts=image.crop(box).getcolors(maxcolors=1_000_000)
        return sum(count for count,pixel in counts if pixel==color)>50

    dark=capture('dark',True)
    light=capture('light',False)
    for image,bg,ink,lanes in ((dark,(0,0,0),(244,247,250),(217,224,227)),
                              (light,(255,255,255),(45,52,54),(236,240,241))):
        assert image.getpixel((1000,1000))==bg, 'Incorrect background color'
        assert contains(image,(40,80,500,300),ink), 'Incorrect speed text color'
        assert contains(image,(750,0,1050,350),lanes), 'Incorrect neutral lane color'
        face=(255,255,255) if image is dark else (236,240,241)
        assert image.getpixel((1638,100))==face, 'Incorrect speed-limit sign face'
        track=(43,50,54) if image is dark else (236,240,241)
        power=(184,193,197) if image is dark else (45,52,54)
        empty=(37,42,45) if image is dark else (236,240,241)
        assert image.getpixel((28,200))==track, 'Incorrect power-track color'
        assert image.getpixel((28,400))==power, 'Incorrect power-fill color'
        assert contains(image,(1680,900,1800,1080),ink), 'Incorrect gear color'
        assert contains(image,(170,940,280,1010),power), 'Incorrect battery-percentage color'
        assert image.getpixel((125,975))==empty, 'Incorrect empty-battery color'
        assert image.getpixel((75,975))==(92,189,104), 'Battery charge is no longer green'
    for enabled in (True,False):
        image=capture(f'assist-{enabled}',enabled,True)
        assert contains(image,(750,0,1050,350),(0,113,255)), 'Autopilot blue changed with theme'
    for name,start,button,expected in (('dark-to-light',True,40,light),
                                        ('light-to-dark',False,20,dark)):
        image=capture(name,start,False,f'--pointer=click@{button},20','--advance=2')
        error=ImageChops.difference(image,expected)
        assert max(ImageStat.Stat(error).mean)<.001, 'Live theme switch did not update all colors'
    print('Actual Rive theme checks passed: exact colors, OLED black, assist blue and live switching.')


if __name__=='__main__':
    main()
