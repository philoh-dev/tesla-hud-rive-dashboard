#!/usr/bin/env python3
"""Exercise live Autopilot updates on the main and nested road artboards."""
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET

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
    local = ROOT / '.tooling' / ('rive.exe' if os.name == 'nt' else 'rive')
    cli = os.environ.get('RIVE_CLI') or (str(local) if local.exists() else shutil.which('rive'))
    if not cli:
        raise SystemExit('Install Rive CLI or set RIVE_CLI.')

    def capture(name, active, dark, *events):
        path, dump = output / (name + '.png'), output / (name + '.json')
        subprocess.run([cli, str(output), f'--screenshot={path}', f'--data-dump={dump}',
                        '--viewport=1800x1080', '--data=gear=4', '--data=egoSpeed=0',
                        '--data=leftBlinker=2', '--data=rightBlinker=1',
                        '--data=accSetSpeed=130', '--data=selfdriveActive=false',
                        f'--data=darkMode={str(dark).lower()}',
                        f'--data=adasOn={str(active).lower()}', '--advance=3', *events],
                       check=True)
        values = {p['name']: p['value'] for p in
                  json.loads(dump.read_text())['viewModel']['properties']}
        return Image.open(path).convert('RGB'), values

    def blue_count(image, box):
        return sum(count for count, (r, g, b) in image.crop(box).getcolors(1_000_000)
                   if b > 160 and b > r * 1.5 and b > g * 1.2)

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
                f'{dark}/{name}: cruise MAX did not follow adasOn'
        for name, events, expected in (
            ('selfdrive-on', ('--pointer=click@60,20',), True),
            ('selfdrive-off', ('--pointer=click@60,20', '--pointer=click@80,20'), False),
            ('unknown-set-speed', ('--pointer=click@60,20', '--pointer=click@100,20'), False),
            ('known-set-speed', ('--pointer=click@60,20', '--pointer=click@100,20',
                                 '--pointer=click@120,20'), True),
            ('handoff-to-selfdrive', ('--pointer=click@20,20', '--pointer=click@60,20',
                                       '--pointer=click@40,20'), True),
        ):
            image, values = capture(f'{dark}-{name}', False, dark, *events, '--advance=2')
            assert (blue_count(image, (1350, 90, 1510, 300)) > 50) == expected, \
                f'{dark}/{name}: cruise MAX visibility incorrect'
            assert not values['adasOn'], 'selfdrive fixture unexpectedly changed adasOn'
        low, values = capture(f'{dark}-set-speed-80', True, dark,
                              '--pointer=click@120,20', '--advance=2')
        high, _ = capture(f'{dark}-set-speed-130', True, dark, '--advance=2')
        assert values['accSetSpeed'] == 80
        assert low.crop((1350, 70, 1530, 180)).tobytes() != high.crop((1350, 70, 1530, 180)).tobytes(), \
            'Cruise value did not redraw after a live set-speed update'
    print('Autopilot runtime checks passed: badge and lanes, initial/live/repeated updates, both themes.')
    print('Cruise runtime checks passed: either assist flag, unknown speed hidden, live value changes, both themes.')


if __name__ == '__main__':
    main()
