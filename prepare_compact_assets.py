"""One-time derivative preparation: Pillow and fonttools==4.67.0 required.

Normal builds use the committed outputs and need only the Python standard library.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent


def main():
    out = ROOT / 'assets/optimized'
    out.mkdir(exist_ok=True)
    for filename in ('Inter-Regular.ttf', 'Inter-Medium.ttf', 'Inter-SemiBold.ttf'):
        font = TTFont(ROOT / 'fonts' / filename)
        options = subset.Options()
        options.recalc_timestamp = False
        options.name_IDs = ['*']
        options.name_legacy = True
        options.layout_features = ['*']  # Includes dashboard's tnum tabular figures.
        sub = subset.Subsetter(options=options)
        # Latin-1, punctuation/spaces (including thin space), minus and fallback.
        sub.populate(unicodes=list(range(0x20, 0x100)) + list(range(0x2000, 0x2070)) + [0x2212, 0xFFFD])
        sub.subset(font)
        font.save(out / filename)
    image = Image.open(ROOT / 'assets/vehicle/model-y-juniper-stealth-grey/drive-chase.png')
    image.resize((640, 585), Image.Resampling.LANCZOS).save(out / 'drive-chase.png', optimize=True)
    manifest = {p.relative_to(out).as_posix(): {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                for p in sorted(out.rglob('*')) if p.suffix in ('.png', '.ttf')}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(manifest)


if __name__ == '__main__':
    main()
