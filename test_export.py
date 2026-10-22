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
            compact_document(doc)
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


if __name__ == '__main__':
    unittest.main()
