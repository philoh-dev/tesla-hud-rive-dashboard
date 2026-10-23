"""Compact packaging keeps layout, bindings and runtime text intact."""
import hashlib
import json
from pathlib import Path
import unittest
from generate import ROOT, Scene
from optimize_export import compact_document
from universal import UniversalScene
from juniper_variants import PROJECTED_JUNIPERS


class CompactExportTest(unittest.TestCase):
    def test_compact_assets_match_manifest(self):
        folder = ROOT / 'assets/optimized'
        for name, info in json.loads((folder / 'manifest.json').read_text()).items():
            data = (folder / name).read_bytes()
            self.assertEqual(len(data), info['bytes'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), info['sha256'])
            if name.endswith('.ttf'):
                self.assertIn(b'tnum', data, 'Keep the dashboard tabular-number feature')

    def test_packaging_preserves_image_dimensions_and_bindings(self):
        for scene in (*(Scene(v) for v in PROJECTED_JUNIPERS), UniversalScene()):
            doc = scene.build()
            images = {i.get('id'): dict(i.attrib) for i in doc.iter('Image')}
            bindings = [dict(b.attrib) for b in doc.iter('DataBindContext')]
            assets = {a.get('id'): a.get('file') for a in doc.iter('ImageAsset')}
            compact_document(doc,trim_textures=False)
            self.assertEqual(bindings, [dict(b.attrib) for b in doc.iter('DataBindContext')])
            for image in doc.iter('Image'):
                before = images[image.get('id')]
                if assets[image.get('assetId')].endswith('/drive-chase.png'):
                    for key, old_size, new_size in (('scaleX', 1312, 640), ('scaleY', 1199, 585)):
                        self.assertAlmostEqual(float(before.get(key, '1'))*old_size,
                                               float(image.get(key))*new_size)
                    for key in ('x', 'y', 'rotation'):
                        self.assertEqual(image.get(key), before.get(key))
                else:
                    self.assertEqual(dict(image.attrib), before)
            for asset in (*doc.iter('ImageAsset'), *doc.iter('FontAsset')):
                self.assertTrue(Path(asset.get('file')).is_file())

    def test_texture_metadata_and_lossless_crop_registration(self):
        records=json.loads((ROOT/'assets/optimized/textures.json').read_text())
        for source,info in records.items():
            self.assertEqual(hashlib.sha256((ROOT/source).read_bytes()).hexdigest(),info['source_sha256'])
            data=(ROOT/info['file']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(),info['sha256'])
            self.assertEqual([int.from_bytes(data[16:20],'big'),int.from_bytes(data[20:24],'big')],info['size'])
        for vehicle in PROJECTED_JUNIPERS:
            doc=compact_document(Scene(vehicle).build(),trim_textures=False)
            images={i.get('id'):dict(i.attrib) for i in doc.iter('Image')}
            assets={a.get('id'):a.get('file') for a in doc.iter('ImageAsset')}
            bindings=[dict(b.attrib) for b in doc.iter('DataBindContext')]
            from optimize_export import trim_and_share_textures
            trim_and_share_textures(doc)
            self.assertEqual(bindings,[dict(b.attrib) for b in doc.iter('DataBindContext')])
            outputs={a.get('id'):a.get('file') for a in doc.iter('ImageAsset')}
            self.assertEqual(len(outputs),10)
            self.assertEqual(len(set(outputs.values())),10)
            for image in doc.iter('Image'):
                before=images[image.get('id')]
                info=records[Path(assets[before['assetId']]).relative_to(ROOT).as_posix()]
                self.assertEqual(outputs[image.get('assetId')],(ROOT/info['file']).as_posix())
                for axis,index,scale,origin in (('x',0,'scaleX','originX'),('y',1,'scaleY','originY')):
                    # Position of the retained source texel stays identical,
                    # including bottom-aligned Park and mirrored steering poses.
                    factor=float(before.get(scale,'1'))
                    anchor=float(before.get(origin,'.5'))
                    old=float(before.get(axis,'0'))+(info['crop'][index]+.5-info['source_size'][index]*anchor)*factor
                    new=float(image.get(axis,'0'))+(.5-info['size'][index]*anchor)*factor
                    self.assertAlmostEqual(old,new,places=9)
            rgba=sum(records[Path(p).relative_to(ROOT).as_posix()]['source_size'][0]*
                     records[Path(p).relative_to(ROOT).as_posix()]['source_size'][1]*4 for p in assets.values())
            trimmed=sum(int.from_bytes(Path(p).read_bytes()[16:20],'big')*
                        int.from_bytes(Path(p).read_bytes()[20:24],'big')*4 for p in outputs.values())
            self.assertLess(trimmed,rgba*.8)


if __name__ == '__main__':
    unittest.main()
