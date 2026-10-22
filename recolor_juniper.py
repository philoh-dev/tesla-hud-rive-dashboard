"""Paint-only pixel recoloring, explicitly approved by the user.

Requires Pillow for regeneration; normal Rive builds remain stdlib-only.
Original Stealth Grey artwork is always the source, never another recolor.
"""
from pathlib import Path
import argparse
import hashlib
import json
from PIL import Image, ImageDraw, ImageFilter

ROOT=Path(__file__).resolve().parent
TEMPLATE=ROOT/'assets/vehicle/model-y-juniper-stealth-grey'
PAINTS={
    'white-multi-coat':(.30,(1.,1.,1.)),
    'diamond-black':(1.65,(1.,1.,1.)),
    'marine-blue':(.85,(.28,.48,1.)),
    'quicksilver':(.55,(1.,1.,1.)),
    'ultra-red':(.82,(1.,.15,.19)),
}
# Glass, wheels and trim exclusions are measured on the immutable templates.
EXCLUSIONS={
    'park.png':[
        [(88,132),(98,94),(132,72),(191,53),(251,48),(310,54),(354,67),(374,78),(350,82),(321,92),(285,113),(253,133),(225,155),(214,171),(191,167),(157,158),(122,147)],
        [(228,148),(253,128),(291,107),(329,91),(362,82),(380,83),(361,106),(328,130),(294,151),(261,168),(230,178)],
        [(157,267),(157,249),(165,231),(179,223),(192,224),(207,234),(213,254),(211,275),(201,295),(185,307),(169,304),(157,292)],
        [(356,190),(360,171),(371,157),(383,153),(395,159),(400,174),(396,196),(386,218),(374,230),(362,227),(357,214)],
        [(5,245),(117,269),(132,286),(108,280),(44,263),(4,251)],
        [(129,255),(136,255),(130,281),(123,281)],
    ],
    'drive-chase.png':[
        [(433,148),(879,148),(901,185),(942,562),(869,577),(442,577),(370,565),(402,190)],
        [(386,191),(337,263),(314,422),(334,484),(364,418)],
        [(926,191),(975,263),(998,422),(978,484),(948,418)],
        [(181,720),(202,740),(223,846),(267,943),(261,1007),(179,1007)],
        [(1131,720),(1110,740),(1089,846),(1045,943),(1051,1007),(1133,1007)],
        [(230,273),(286,260),(324,275),(316,333),(245,341),(226,319)],
        [(1082,273),(1026,260),(988,275),(996,333),(1067,341),(1086,319)],
        [(342,874),(974,874),(1008,926),(963,935),(349,935),(304,927)],
    ],
    'view-angles/ego-back-left-middle.png':[
        [(110,20),(305,16),(320,34),(352,186),(290,196),(132,194),(103,188),(109,94)],
        [(92,29),(103,22),(104,93),(85,143),(64,152),(58,140),(69,85)],
        [(319,38),(330,58),(344,114),(350,149),(348,168),(340,145)],
        [(16,199),(27,206),(36,278),(73,326),(74,386),(15,386)],
        [(401,279),(423,291),(432,336),(427,386),(374,386),(376,345)],
        [(5,84),(12,77),(40,71),(48,79),(46,102),(9,107)],
        [(352,76),(373,78),(391,94),(392,101),(358,103)],
        [(104,315),(368,317),(390,344),(353,352),(104,350),(79,343)],
    ],
}


def paint_mask(image,view):
    mask=Image.new('L',image.size,255)
    draw=ImageDraw.Draw(mask)
    for polygon in EXCLUSIONS[view]:
        draw.polygon(polygon,fill=0)
    # The canopy/roof at the very top stays dark glass.
    top={'park.png':47,'drive-chase.png':148,'view-angles/ego-back-left-middle.png':16}[view]
    draw.rectangle((0,0,image.width,top),fill=0)
    return mask.filter(ImageFilter.GaussianBlur(.65))


def pixels(image):
    return image.get_flattened_data() if hasattr(image,'get_flattened_data') else image.getdata()


def recolor(image,mask,paint):
    gamma,tint=PAINTS[paint]
    result=image.copy()
    output=[]
    for (r,g,b,a),m in zip(pixels(image),pixels(mask)):
        # Leave transparent pixels, dark trim/seams, and saturated lamps intact.
        if not a or not m or max(r,g,b)-min(r,g,b)>max(30,max(r,g,b)*.35):
            output.append((r,g,b,a));continue
        light=.2126*r+.7152*g+.0722*b
        strength=m/255*min(1,max(0,(light-20)/30))
        mapped=255*(light/255)**gamma
        highlight=max(0,(light-135)/120)
        rgb=[mapped*(c*(1-highlight)+highlight) for c in tint]
        output.append(tuple(round(old*(1-strength)+new*strength) for old,new in zip((r,g,b),rgb))+(a,))
    result.putdata(output)
    assert image.getchannel('A').tobytes()==result.getchannel('A').tobytes()
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('paint',choices=PAINTS)
    args=parser.parse_args()
    vehicle='model-y-juniper-'+args.paint
    folder=ROOT/'assets/vehicle'/vehicle
    masks=TEMPLATE/'paint-masks';masks.mkdir(exist_ok=True)
    for view in EXCLUSIONS:
        source=Image.open(TEMPLATE/view).convert('RGBA')
        mask=paint_mask(source,view)
        mask.save(masks/(Path(view).stem+'.png'))
        target=folder/view;target.parent.mkdir(parents=True,exist_ok=True)
        result=recolor(source,mask,args.paint)
        assert result.size==source.size
        for before,after,m in zip(pixels(source),pixels(result),pixels(mask)):
            if not m:
                assert before==after, 'Unmasked glass/trim must remain byte-identical'
        result.save(target,optimize=True)
    compact=ROOT/'assets/optimized'/vehicle;compact.mkdir(parents=True,exist_ok=True)
    Image.open(folder/'drive-chase.png').resize((640,585),Image.Resampling.LANCZOS).save(compact/'drive-chase.png',optimize=True)
    registry=ROOT/'juniper_variants.py'
    namespace={}
    exec(registry.read_text(),namespace)
    vehicles=tuple(dict.fromkeys((*namespace['PROJECTED_JUNIPERS'],vehicle)))
    registry.write_text('"""Juniper colors promoted to the approved Stealth Grey scene template."""\n'
                        +'PROJECTED_JUNIPERS = '+repr(vehicles)+'\n',encoding='utf-8')
    from generate import VEHICLES,vehicle_assets,DEFAULT_VEHICLE
    from vehicle_angles import POSE_ASSETS
    paths={p for v in VEHICLES for p in vehicle_assets(v).values()}
    paths.update(POSE_ASSETS.values())
    paths.update(f'assets/vehicle/{v}/view-angles/ego-back-left-middle.png' for v in vehicles if v!=DEFAULT_VEHICLE)
    paths.update('fonts/'+name for name in ('Inter-Regular.ttf','Inter-Medium.ttf','Inter-SemiBold.ttf','Inter-OFL.txt'))
    manifest=ROOT/'assets/manifest.json'
    data=json.loads(manifest.read_text())
    data['sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)}
    manifest.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    manifest=ROOT/'assets/optimized/manifest.json'
    data=json.loads(manifest.read_text())
    output=compact/'drive-chase.png'
    data[output.relative_to(manifest.parent).as_posix()]={'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}
    manifest.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    (folder/'README.md').write_text(f'''# Model Y Juniper - {args.paint}

Generated by `python recolor_juniper.py {args.paint}` from the approved Stealth
Grey Park, rear chase and intermediate steering poses. Only masked paint pixels
change; every original alpha pixel and canvas dimension is preserved. Glass,
tires, lamps and trim are excluded. These are deterministic recolors, with no
image generation or geometry changes. Both steering directions use the same
mirrored intermediate pose, selected only beyond +/-50 degrees.

The dashboard shares the Stealth Grey projected road, blind-spot cars, contact
shadows, 20%-lower ego position and blind-spot-only vibration. Full sources stay
in this folder; compact export artwork is in `assets/optimized/{vehicle}`.
''',encoding='utf-8')
    print(vehicle)


if __name__=='__main__':
    main()
