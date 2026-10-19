"""Asset fidelity and Newhaven composition regression checks (stdlib only)."""
import unittest
import math
import hashlib
import json
import xml.etree.ElementTree as ET

from generate import ASSETS, ROOT, Scene, ROAD_RATE, PROPERTIES, IDS, VEHICLES, vehicle_assets


class NewhavenDesignTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scene = Scene().build()

    def test_bundled_assets_match_original_source_checksums(self):
        manifest=json.loads((ROOT/'assets/manifest.json').read_text())
        expected={path for vehicle in VEHICLES for path in vehicle_assets(vehicle).values()}
        expected.update(f'fonts/{name}' for name in ('Montserrat-Light.ttf','Montserrat-Bold.ttf','OFL.txt'))
        self.assertEqual(set(manifest['sha256']),expected)
        for path,digest in manifest['sha256'].items():
            with self.subTest(asset=path):
                self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest)

    def test_all_vehicle_views_use_original_image_assets(self):
        names = {image.get('name') for image in self.scene.iter('Image')}
        for name in ('Park front three-quarter vehicle', 'Driving ego vehicle',
                     'left red vehicle', 'left grey vehicle', 'right red vehicle', 'right grey vehicle'):
            self.assertIn(name, names)

    def test_each_vehicle_changes_only_ego_assets(self):
        for vehicle in VEHICLES:
            with self.subTest(vehicle=vehicle):
                scene=Scene(vehicle).build()
                assets={asset.get('name'):asset.get('file') for asset in scene.iter('ImageAsset')}
                self.assertEqual(assets,vehicle_assets(vehicle))
                for name,path in ASSETS.items():
                    if name not in ('ego','park'):
                        self.assertEqual(assets[name],path)
                for asset in scene.iter('ImageAsset'):
                    if asset.get('name') in ('ego','park'):
                        asset.set('file',ASSETS[asset.get('name')])
                self.assertEqual(ET.tostring(scene),ET.tostring(Scene().build()))

    def test_unknown_vehicle_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'Unsupported vehicle'):
            Scene('../unknown')

    def test_original_aspect_and_80_20_regions(self):
        main = self.scene.find("Artboard[@name='Newhaven']")
        self.assertEqual((main.get('width'), main.get('height')), ('1800','1080'))
        main_region = main.find(".//LayoutComponent[@name='Driving region 80 percent']")
        footer = main.find(".//LayoutComponent[@name='Invisible status region 20 percent']")
        self.assertEqual(main_region.get('fractionalHeight'), '4')
        self.assertEqual(footer.get('fractionalHeight'), '1')
        for region in (main_region,footer):
            style=region.find('LayoutComponentStyle')
            self.assertEqual(style.get('layoutHeightScaleType'),'fill')

    def test_edges_and_center_use_independent_responsive_columns(self):
        for name in ('Left edge','Right edge','Battery left','Gear right'):
            box=self.scene.find(f".//LayoutComponent[@name='{name}']")
            self.assertEqual(box.find('LayoutComponentStyle').get('layoutWidthScaleType'),'fill')
        for name in ('Right edge','Gear right'):
            style=self.scene.find(f".//LayoutComponent[@name='{name}']/LayoutComponentStyle")
            self.assertEqual(style.get('layoutAlignmentType'),'topRight')
        for name in ('Road center','Autopilot center'):
            box=self.scene.find(f".//LayoutComponent[@name='{name}']")
            self.assertEqual(box.get('width'),'0')

    def test_host_theme_setting_drives_background_speed_and_neutral_lanes(self):
        self.assertEqual(PROPERTIES['darkMode'],('Boolean',True))
        self.assertIn('darkModeBackgroundGray',PROPERTIES)
        main=self.scene.find("Artboard[@name='Newhaven']")
        background=main.find('Fill/SolidColor')
        speed=main.find(".//Text[@name='Current speed']/TextStylePaint/Fill/SolidColor")
        self.assertEqual(background.get('colorValue'),'FF000000')
        neutral=self.scene.findall(".//Node[@name='Neutral lanes']//SolidColor")
        face=main.find(".//Shape[@name='Sign face']/Fill/SolidColor")
        for color in (background,speed,face,*neutral):
            bindings=color.findall('DataBindContext')
            self.assertEqual({b.get('propertyKey') for b in bindings},{'118','136','210'})
            self.assertTrue(all(b.get('sourcePathIds')==f"1:1-{IDS['darkMode']}" for b in bindings))
        for color in self.scene.findall(".//Node[@name='Assist lanes']//SolidColor"):
            self.assertEqual(color.get('colorValue'),'FF0071FF')
            self.assertEqual(color.findall('DataBindContext'),[])

    def test_no_substitute_theme_or_script(self):
        text = ET.tostring(self.scene, encoding='unicode')
        self.assertNotIn('HORIZON', text)
        self.assertNotIn('<Script', text)
        for name in ('Identity', 'Power caption', 'Gear caption', 'Active blue disk'):
            self.assertNotIn(f'name="{name}"', text)

    def test_smaller_limit_font_and_centered_autopilot(self):
        limit = self.scene.find(".//Text[@name='Speed limit value']/TextStylePaint")
        self.assertEqual(limit.get('fontSize'), '36')
        anchor = self.scene.find(".//Node[@name='Autopilot anchor']")
        self.assertEqual((anchor.get('scaleX'), anchor.get('scaleY')), ('2.025', '2.025'))
        self.assertEqual((anchor.get('x'), anchor.get('y')), ('0', '108'))
        border = self.scene.find(".//Shape[@name='Sign red border']/Ellipse")
        self.assertEqual((border.get('width'), border.get('height')), ('96', '96'))

    def test_generated_source_is_reproducible(self):
        ET.indent(self.scene, space='  ')
        self.assertEqual((ROOT/'scene.rml').read_text(encoding='utf-8'),
                         ET.tostring(self.scene, encoding='unicode') + '\n')

    def test_no_vehicle_transition_or_intermediate_assets_are_shipped(self):
        main = self.scene.find("Artboard[@name='Newhaven']")
        cue_ids={n.get('id') for n in main.iter('Node')
                 if n.get('name') in ('Forward direction motion','Reverse direction motion')}
        self.assertTrue(all(obj.get('objectId') in cue_ids for obj in main.iter('KeyedObject')))
        self.assertEqual(list(self.scene.iter('ListenerViewModelChange')),[])
        self.assertEqual(len(list(self.scene.iter('ImageAsset'))),len(ASSETS))
        self.assertFalse(any('turntable/' in a.get('file','') for a in self.scene.iter('ImageAsset')))
        self.assertFalse((ROOT/'assets/turntable').exists())
        self.assertFalse((ROOT/'prepare_turntable.py').exists())

    def test_departure_cues_move_and_fade_over_four_tenths_of_a_second(self):
        for label,offset in (('Forward',-40),('Reverse',40)):
            animation=self.scene.find(f".//LinearAnimation[@name='{label} direction departing']")
            self.assertEqual((animation.get('duration'),animation.get('fps')),('24','60'))
            for key,end in (('18',0),('14',offset)):
                frames=animation.findall(f"KeyedObject/KeyedProperty[@propertyKey='{key}']/KeyFrameDouble")
                self.assertEqual([int(f.get('frame')) for f in frames],[0,24])
                self.assertEqual(float(frames[-1].get('value')),end)

    def test_static_vehicles_switch_directly_from_gear(self):
        for name,formula in (('Park front three-quarter vehicle','Park vehicle visible'),
                             ('Driving ego vehicle','Driving vehicle visible')):
            image=self.scene.find(f".//Image[@name='{name}']")
            binding=image.find('DataBindContext')
            self.assertEqual(binding.get('propertyKey'),'18')
            converter=self.scene.find(f"DataConverterFormula[@id='{binding.get('converterId')}']")
            self.assertEqual(converter.get('name'),formula)
        park=self.scene.find(".//Image[@name='Park front three-quarter vehicle']")
        self.assertEqual((park.get('x'),park.get('y'),park.get('originY')),('400','384','1'))

    def test_park_hides_the_whole_speed_and_power_cluster(self):
        cluster = self.scene.find(".//Node[@name='Speed and power']")
        binding = cluster.find('DataBindContext')
        self.assertEqual(binding.get('propertyKey'),'18')
        converter = self.scene.find(f"DataConverterFormula[@id='{binding.get('converterId')}']")
        self.assertEqual(converter.get('name'),'Instruments outside Park')
        self.assertIsNotNone(cluster.find("Text[@name='Current speed']"))
        for name in ('Consumption fill','Recuperation fill','Power track'):
            self.assertIsNotNone(cluster.find(f"Shape[@name='{name}']"))

    def test_road_switches_immediately_but_retains_speed_driven_motion(self):
        road = self.scene.find(".//NestedArtboard[@name='Speed driven road']")
        self.assertIsNotNone(road.find("DataBindContext[@propertyKey='18']"))
        playback=road.find('NestedSimpleAnimation')
        self.assertEqual(playback.get('isPlaying'),'true')
        self.assertEqual(playback.get('animationId'),'4:3')
        self.assertIsNotNone(playback.find("DataBindContext[@propertyKey='199']"))
        self.assertIsNotNone(self.scene.find(".//LinearAnimation[@name='One 12 metre road cycle']"))

    def test_road_rate_matches_twelve_metre_firmware_cycle(self):
        def rate(speed,gear=4,imperial=False):
            return eval(ROAD_RATE,{'__builtins__':{}},dict(egoSpeed=speed,gear=gear,
                        isImperial=imperial,max=max,min=min,sqrt=math.sqrt,pow=pow))
        self.assertEqual(rate(0),0)
        self.assertAlmostEqual(rate(43.2),1)
        self.assertAlmostEqual(rate(86.4),2)
        self.assertAlmostEqual(rate(43.2,2),-1)
        self.assertAlmostEqual(rate(60,imperial=True),rate(96.56064))
        for gear in (0,1,3):
            self.assertEqual(rate(100,gear),0)

    def test_lane_motion_preserves_straight_boundaries_and_tapers(self):
        road=self.scene.find("Artboard[@name='Road motion']")
        animation=road.find('LinearAnimation')
        self.assertEqual(animation.get('fps'),'60')
        self.assertEqual(len(road.findall('.//Shape')),28)
        self.assertEqual(len(animation.findall("KeyedObject/KeyedProperty[@propertyKey='47']")),28)
        for vertex in road.iter('StraightVertex'):
            x,y=float(vertex.get('x')),float(vertex.get('y'))
            self.assertAlmostEqual(abs(x-400),50+y*55/384)

    def test_rejected_motion_interpolation_is_not_shipped(self):
        motion = [a for a in self.scene.iter('ImageAsset') if '/motion/' in a.get('file','')]
        self.assertEqual(motion,[])


if __name__ == '__main__':
    unittest.main()
