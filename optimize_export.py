"""Prepare compact export sources without changing editable dashboard artwork."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent


def compact_document(doc,trim_textures=True):
    ego_ids = set()
    for asset in (*doc.iter('ImageAsset'), *doc.iter('FontAsset')):
        path = asset.get('file')
        if asset.tag == 'FontAsset':
            path = 'assets/optimized/' + Path(path).name
        elif path.endswith('/drive-chase.png'):
            ego_ids.add(asset.get('id'))
            vehicle=Path(path).parent.name
            path = ('assets/optimized/drive-chase.png' if vehicle=='model-y-juniper-stealth-grey'
                    else f'assets/optimized/{vehicle}/drive-chase.png')
        asset.set('file', (ROOT / path).as_posix())
    for image in doc.iter('Image'):
        if image.get('assetId') in ego_ids:
            # Rive image coordinates use the raster's native size. Keep its
            # displayed dimensions and center identical after downsampling.
            for key, ratio in (('scaleX', 1312/640), ('scaleY', 1199/585)):
                assert image.find(f"DataBindContext[@propertyKey='{16 if key == 'scaleX' else 17}']") is None
                image.set(key, str(float(image.get(key, '1')) * ratio))
    if trim_textures and any(s.get('name','').endswith(' exclusive poses') for s in doc.iter('Solo')):
        trim_and_share_textures(doc)
    return doc


def trim_and_share_textures(doc):
    records=json.loads((ROOT/'assets/optimized/textures.json').read_text())
    metadata={}
    canonical={}
    references={}
    for asset in list(doc.findall('ImageAsset')):
        source=Path(asset.get('file')).relative_to(ROOT).as_posix()
        info=records[source]
        identity=asset.get('id')
        metadata[identity]=info
        asset.set('file',(ROOT/info['file']).as_posix())
        if info['file'] in canonical:
            references[identity]=canonical[info['file']]
            doc.remove(asset)
        else:
            canonical[info['file']]=identity
    for image in doc.iter('Image'):
        identity=image.get('assetId')
        info=metadata[identity]
        assert float(image.get('rotation','0'))==0
        assert not any(b.get('propertyKey') in ('13','14','15','16','17') for b in image.findall('DataBindContext'))
        for axis,index,scale,origin in (('x',0,'scaleX','originX'),('y',1,'scaleY','originY')):
            size=info['size'][index]
            original=info['source_size'][index]
            offset=info['crop'][index]+(size-original)*float(image.get(origin,'.5'))
            image.set(axis,str(float(image.get(axis,'0'))+offset*float(image.get(scale,'1'))))
        image.set('assetId',references.get(identity,identity))


def prepare_export():
    doc = compact_document(ET.parse(ROOT / 'scene.rml').getroot())
    folder = ROOT / 'build/compact-export'
    folder.mkdir(parents=True, exist_ok=True)
    ET.indent(doc, space='  ')
    ET.ElementTree(doc).write(folder / 'scene.rml', encoding='utf-8')
    (folder / 'rive.yaml').write_text('name: thud_dashboard\nmain: Newhaven\n', encoding='utf-8')
    return folder
