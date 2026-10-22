"""Prepare compact export sources without changing editable dashboard artwork."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent


def compact_document(doc):
    ego_ids = set()
    for asset in (*doc.iter('ImageAsset'), *doc.iter('FontAsset')):
        path = asset.get('file')
        if asset.tag == 'FontAsset':
            path = 'assets/optimized/' + Path(path).name
        elif path.endswith('/model-y-juniper-stealth-grey/drive-chase.png'):
            ego_ids.add(asset.get('id'))
            path = 'assets/optimized/drive-chase.png'
        asset.set('file', (ROOT / path).as_posix())
    for image in doc.iter('Image'):
        if image.get('assetId') in ego_ids:
            # Rive image coordinates use the raster's native size. Keep its
            # displayed dimensions and center identical after downsampling.
            for key, ratio in (('scaleX', 1312/640), ('scaleY', 1199/585)):
                assert image.find(f"DataBindContext[@propertyKey='{16 if key == 'scaleX' else 17}']") is None
                image.set(key, str(float(image.get(key, '1')) * ratio))
    return doc


def prepare_export():
    doc = compact_document(ET.parse(ROOT / 'scene.rml').getroot())
    folder = ROOT / 'build/compact-export'
    folder.mkdir(parents=True, exist_ok=True)
    ET.indent(doc, space='  ')
    ET.ElementTree(doc).write(folder / 'scene.rml', encoding='utf-8')
    (folder / 'rive.yaml').write_text('name: thud_dashboard\nmain: Newhaven\n', encoding='utf-8')
    return folder
