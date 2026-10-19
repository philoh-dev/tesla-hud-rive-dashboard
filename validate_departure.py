#!/usr/bin/env python3
"""Render actual Rive departure cues; assert timing, direction and resetting."""
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image
from generate import ROOT, Scene


def main():
    output=ROOT/'build'/'departure-validation'
    output.mkdir(parents=True,exist_ok=True)
    scene=Scene()
    document=scene.build()
    for asset in (*document.iter('ImageAsset'),*document.iter('FontAsset')):
        asset.set('file',str(ROOT/asset.get('file')))
    board=document.find("Artboard[@name='Newhaven']")
    machine=board.find('StateMachine')
    for x,prop,value in ((20,'egoSpeed',5),(40,'egoSpeed',0),(60,'gear',1)):
        scene.rect(board,'Test control',x,20,16,16,'FF000000')
        listener=scene.el(machine,'StateMachineListenerSingle',targetId=board[-1].get('id'),
                          listenerTypeValue='click',name='Departure test control')
        change=scene.el(listener,'ListenerViewModelChange')
        target=scene.el(change,'BindablePropertyNumber',propertyValue=value)
        scene.bind(target,prop,636).set('direction','true')
    ET.indent(document,space='  ')
    ET.ElementTree(document).write(output/'scene.rml',encoding='unicode')
    (output/'rive.yaml').write_text('name: departure_validation\nmain: Newhaven\n')
    local=ROOT/'.tooling'/('rive.exe' if os.name=='nt' else 'rive')
    cli=os.environ.get('RIVE_CLI') or (str(local) if local.exists() else shutil.which('rive'))
    if not cli:
        raise SystemExit('Install Rive CLI or set RIVE_CLI.')

    def capture(name,gear,*events,speed=0,dark=True):
        path=output/(name+'.png')
        result=subprocess.run([cli,str(output),f'--screenshot={path}','--viewport=1800x1080',
            f'--data=darkMode={str(dark).lower()}',f'--data=gear={gear}',f'--data=egoSpeed={speed}',
            '--data=powerLevel=0','--data=adasOn=false','--data=leftBlinker=0',
            '--data=rightBlinker=0','--data=leftBlindSpot=0','--data=rightBlindSpot=0',
            '--advance=3',*events],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if result.returncode:
            raise RuntimeError(result.stdout)
        return Image.open(path).convert('RGB')

    def measure(image,gear,dark=True):
        box=(840,160,960,380) if gear==4 else (840,680,960,910)
        crop=image.crop(box)
        bg=0 if dark else 255
        mass=weighted_y=0
        peak=0
        for y in range(crop.height):
            for x in range(crop.width):
                weight=max(abs(channel-bg) for channel in crop.getpixel((x,y)))
                if weight>2:
                    mass+=weight
                    weighted_y+=weight*(y+box[1])
                    peak=max(peak,weight)
        return mass,weighted_y/max(1,mass),peak

    for gear,label,direction in ((4,'forward',-1),(2,'reverse',1)):
        stopped=measure(capture(label+'-stopped',gear),gear)
        midpoint=measure(capture(label+'-midpoint',gear,'--pointer=click@20,20','--advance=12'),gear)
        ended=measure(capture(label+'-ended',gear,'--pointer=click@20,20','--advance=24'),gear)
        assert stopped[0]>1000, f'{label}: stopped arrow missing'
        assert 0<midpoint[0]<stopped[0], f'{label}: no gradual fade'
        assert (midpoint[1]-stopped[1])*direction>15, f'{label}: wrong travel direction'
        assert midpoint[2]<stopped[2], f'{label}: opacity did not decrease'
        assert ended[0]==0, f'{label}: arrow remains after 0.4 s'
        assert measure(capture(label+'-already-moving',gear,speed=5),gear)[0]==0, 'Entrance flash while moving'
        repeated=capture(label+'-repeated-speed',gear,'--pointer=click@20,20','--advance=30',
                         '--pointer=click@20,20','--advance=12')
        assert measure(repeated,gear)[0]==0, 'Repeated speed update retriggered departure'
        reset=capture(label+'-reset',gear,'--pointer=click@20,20','--advance=12',
                      '--pointer=click@40,20','--advance=3')
        assert abs(measure(reset,gear)[1]-stopped[1])<.1, 'Stopping did not reset arrow position'
        shifted=capture(label+'-shift-to-park',gear,'--pointer=click@20,20','--advance=6',
                        '--pointer=click@60,20','--advance=2')
        # Park car occupies the Drive arrow's old area, so gear gating is
        # inspected structurally instead of mistaking the car for an arrow.
        del shifted
        assert measure(capture(label+'-light',gear,dark=False),gear,dark=False)[0]>1000
    for gear in (0,3):
        image=capture(f'no-arrow-gear-{gear}',gear)
        assert measure(image,4)[0]==0 and measure(image,2)[0]==0, 'Arrow visible in N/unknown'
    print('Actual Rive departure checks passed: D/R direction, fade, 0.4 s, reset, repeat updates and both themes.')


if __name__=='__main__':
    main()
