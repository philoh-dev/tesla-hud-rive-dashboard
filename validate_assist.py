#!/usr/bin/env python3
"""Exercise live Autopilot updates on the main and nested road artboards."""
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from copy import deepcopy

from PIL import Image
from generate import ROOT, Scene


def main():
    output = ROOT / 'build' / 'assist-validation'
    output.mkdir(parents=True, exist_ok=True)
    scene = Scene()
    document = scene.build()
    for asset in (*document.iter('ImageAsset'), *document.iter('FontAsset')):
        asset.set('file', str(ROOT / asset.get('file')))
    main_board = document.find("Artboard[@name='Newhaven']")
    machine = main_board.find('StateMachine')
    for x, value in ((20, True), (40, False)):
        scene.rect(main_board, 'Assist test control', x, 20, 16, 16, 'FF000000')
        listener = scene.el(machine, 'StateMachineListenerSingle',
                            targetId=main_board[-1].get('id'), listenerTypeValue='click')
        change = scene.el(listener, 'ListenerViewModelChange')
        prop = scene.el(change, 'BindablePropertyBoolean', propertyValue=value)
        scene.bind(prop, 'adasOn', 634).set('direction', 'true')
    for x, name, value, kind, key in (
        (60, 'selfdriveActive', True, 'Boolean', 634),
        (80, 'selfdriveActive', False, 'Boolean', 634),
        (100, 'accSetSpeed', 0, 'Number', 636),
        (120, 'accSetSpeed', 80, 'Number', 636),
        (140, 'accSetSpeed', 130, 'Number', 636),
        (160, 'accSetSpeed', -1, 'Number', 636),
    ):
        scene.rect(main_board, 'Cruise test control', x, 20, 16, 16, 'FF000000')
        listener = scene.el(machine, 'StateMachineListenerSingle',
                            targetId=main_board[-1].get('id'), listenerTypeValue='click')
        change = scene.el(listener, 'ListenerViewModelChange')
        prop = scene.el(change, 'BindableProperty' + kind, propertyValue=value)
        scene.bind(prop, name, key).set('direction', 'true')
    ET.indent(document, space='  ')
    ET.ElementTree(document).write(output / 'scene.rml', encoding='unicode')
    (output / 'rive.yaml').write_text('name: assist_validation\nmain: Newhaven\n')
    # The reference SET badge does not need an assist visibility state machine.
    # Like dash_demo.riv, use an idle-only machine so the CLI binds the VM,
    # without any visibility animation or assist transition.
    idle_machine=output.parent/'assist-idle-machine'
    idle_machine.mkdir(exist_ok=True)
    simple=deepcopy(document)
    board=simple.find("Artboard[@name='Newhaven']")
    board.remove(board.find('StateMachine'))
    machine=scene.el(board,'StateMachine',id=board.get('defaultStateMachineId'),name='Idle only')
    layer=scene.el(machine,'StateMachineLayer',name='Idle')
    scene.el(layer,'AnyState')
    scene.el(layer,'ExitState')
    entry=scene.el(layer,'EntryState')
    scene.el(entry,'StateTransition',stateToId='9:3')
    scene.el(layer,'AnimationState',id='9:3',animationId='9:1')
    scene.el(board,'LinearAnimation',id='9:1',name='Idle',duration=1,fps=60,loopValue='oneShot')
    ET.ElementTree(simple).write(idle_machine/'scene.rml',encoding='unicode')
    (idle_machine/'rive.yaml').write_text('name: assist_validation\nmain: Newhaven\n')
    local = ROOT / '.tooling' / ('rive.exe' if os.name == 'nt' else 'rive')
    cli = os.environ.get('RIVE_CLI') or (str(local) if local.exists() else shutil.which('rive'))
    if not cli:
        raise SystemExit('Install Rive CLI or set RIVE_CLI.')

    def capture(name, active, dark, *events, project=output, set_speed=130):
        path, dump = output / (name + '.png'), output / (name + '.json')
        result=subprocess.run([cli, str(project), f'--screenshot={path}', f'--data-dump={dump}',
                        '--viewport=1800x1080', '--data=gear=4', '--data=egoSpeed=0',
                        '--data=leftBlinker=2', '--data=rightBlinker=1',
                        f'--data=accSetSpeed={set_speed}', '--data=selfdriveActive=false',
                        f'--data=darkMode={str(dark).lower()}',
                        f'--data=adasOn={str(active).lower()}', '--advance=3', *events],
                       stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if result.returncode:
            raise RuntimeError(result.stdout)
        values = {p['name']: p['value'] for p in
                  json.loads(dump.read_text())['viewModel']['properties']}
        return Image.open(path).convert('RGB'), values

    def blue_count(image, box):
        return sum(count for count, (r, g, b) in image.crop(box).getcolors(1_000_000)
                   if b > 160 and b > r * 1.5 and b > g * 1.2)

    def caption_visible(image,dark):
        colors=image.crop((1350,200,1510,270)).getcolors(1_000_000)
        count=sum(n for n,(r,g,b) in colors
                  if (max(r,g,b)>70 if dark else min(r,g,b)<210))
        return count>50

    for dark in (True, False):
        for name, initial, expected, events in (
            ('off', False, False, ()), ('on', True, True, ()),
            ('engage', False, True, ('--pointer=click@20,20', '--advance=2')),
            ('disengage', True, False, ('--pointer=click@40,20', '--advance=2')),
            ('reengage', True, True, ('--pointer=click@40,20', '--advance=1',
                                      '--pointer=click@20,20', '--advance=2')),
        ):
            image, values = capture(f'{dark}-{name}', initial, dark, *events)
            assert values['adasOn'] == expected, 'Fixture failed to update adasOn'
            for label, box in (('badge', (800, 880, 1000, 1080)),
                               ('lanes', (650, 0, 1150, 350))):
                count = blue_count(image, box)
                assert (count > 100) == expected, f'{dark}/{name}: {label} blue pixels={count}'
            assert (blue_count(image, (1350, 90, 1510, 300)) > 50) == expected, \
                f'{dark}/{name}: cruise MAX styling did not follow adasOn'
            assert caption_visible(image,dark),f'{dark}/{name}: positive set speed was hidden by assist state'
        for name, events, expected in (
            ('selfdrive-on', ('--pointer=click@60,20',), True),
            ('selfdrive-off', ('--pointer=click@60,20', '--pointer=click@80,20'), True),
            ('unknown-set-speed', ('--pointer=click@60,20', '--pointer=click@100,20'), False),
            ('negative-set-speed', ('--pointer=click@160,20',), False),
            ('known-set-speed', ('--pointer=click@60,20', '--pointer=click@100,20',
                                 '--pointer=click@120,20'), True),
            ('handoff-to-selfdrive', ('--pointer=click@20,20', '--pointer=click@60,20',
                                       '--pointer=click@40,20'), True),
        ):
            image, values = capture(f'{dark}-{name}', False, dark, *events, '--advance=2')
            assert caption_visible(image,dark) == expected, \
                f'{dark}/{name}: cruise MAX visibility incorrect'
            assert not values['adasOn'], 'selfdrive fixture unexpectedly changed adasOn'
            assert blue_count(image,(1350,90,1510,300))<=50, \
                f'{dark}/{name}: inactive assist caption should be muted, not blue'
        low, values = capture(f'{dark}-set-speed-80', True, dark,
                              '--pointer=click@120,20', '--advance=2')
        high, _ = capture(f'{dark}-set-speed-130', True, dark, '--advance=2')
        assert values['accSetSpeed'] == 80
        assert low.crop((1350, 70, 1530, 180)).tobytes() != high.crop((1350, 70, 1530, 180)).tobytes(), \
            'Cruise value did not redraw after a live set-speed update'
        for speed in (0,80):
            image,_=capture(f'{dark}-idle-machine-{speed}',False,dark,
                            project=idle_machine,set_speed=speed)
            assert caption_visible(image,dark)==(speed>0), \
                f'{dark}: direct set-speed binding depends on assist transitions'
    print('Autopilot runtime checks passed: badge and lanes, initial/live/repeated updates, both themes.')
    print('Cruise runtime checks passed: direct visibility with assist off, zero/negative hidden, live value changes,')
    print('assist styling only, idle-only state machine supported, both themes.')


if __name__ == '__main__':
    main()
