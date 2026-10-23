"""Losslessly trim transparent margins for lower decoded texture memory.

Run after compact image preparation/recoloring. Requires Pillow only here;
normal exports use the committed PNGs and metadata with stdlib Python.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image
from generate import ROOT,Scene
from juniper_variants import PROJECTED_JUNIPERS
from optimize_export import compact_document


def main():
    folder=ROOT/'assets/optimized/textures'
    folder.mkdir(exist_ok=True)
    paths=set()
    for vehicle in PROJECTED_JUNIPERS:
        doc=compact_document(Scene(vehicle).build(),trim_textures=False)
        paths.update(a.get('file') for a in doc.iter('ImageAsset'))
    records={}
    for name in sorted(paths):
        source=Path(name)
        relative=source.relative_to(ROOT).as_posix()
        image=Image.open(source).convert('RGBA')
        left,top,right,bottom=image.getchannel('A').getbbox()
        # Keep a transparent texel border for bilinear sampling at edges.
        crop=(max(0,left-1),max(0,top-1),min(image.width,right+1),min(image.height,bottom+1))
        target=folder/(hashlib.sha256(relative.encode()).hexdigest()[:12]+'-'+source.name)
        cropped=image.crop(crop)
        cropped.save(target,optimize=True)
        records[relative]={'file':target.relative_to(ROOT).as_posix(),
                           'source_size':list(image.size),'crop':list(crop),
                           'size':list(cropped.size),
                           'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                           'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
    (ROOT/'assets/optimized/textures.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    print(f'Prepared {len(records)} unique texture derivatives')


if __name__=='__main__':
    main()
