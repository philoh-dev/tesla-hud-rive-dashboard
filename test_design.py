"""Asset fidelity and Newhaven composition regression checks (stdlib only)."""
import unittest
import math
import hashlib
import json
import xml.etree.ElementTree as ET

from generate import (ASSETS, ROOT, Scene, ROAD_RATE, ROAD_BEND, ROAD_BEND_ANCHOR,
                      ROAD_BEND_PIXELS, ROAD_STEERING_SMOOTHING, PROPERTIES, IDS,
                      VEHICLES, JUNIPER_VEHICLES, vehicle_assets, turn_signal_points, FORMULAS)


class NewhavenDesignTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scene = Scene().build()

    def test_bundled_assets_match_original_source_checksums(self):
        manifest=json.loads((ROOT/'assets/manifest.json').read_text())
        expected={path for vehicle in VEHICLES for path in vehicle_assets(vehicle).values()}
        from vehicle_angles import POSE_ASSETS
        expected.update(POSE_ASSETS.values())
        expected.update(f'fonts/{name}' for name in ('Inter-Regular.ttf','Inter-Medium.ttf',
                                                    'Inter-SemiBold.ttf','Inter-OFL.txt'))
        self.assertEqual(set(manifest['sha256']),expected)
        for path,digest in manifest['sha256'].items():
            with self.subTest(asset=path):
                self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest)

    def test_all_vehicle_views_use_original_image_assets(self):
        names = {image.get('name') for image in self.scene.iter('Image')}
        for name in ('Park front three-quarter vehicle', 'Driving ego vehicle',
                     'left red vehicle', 'left grey vehicle', 'right red vehicle', 'right grey vehicle'):
            self.assertIn(name, names)

    def test_other_vehicles_keep_shared_assets_and_layout(self):
        expected=Scene(VEHICLES[1]).build()
        for asset in expected.iter('ImageAsset'):
            if asset.get('name') in ('ego','park'):
                asset.set('file',ASSETS[asset.get('name')])
        parent=expected.find(".//Node[@name='Native 800 pixel scene']")
        parent.remove(parent.find("Node[@name='Park ground']"))
        for vehicle in (v for v in VEHICLES if v not in JUNIPER_VEHICLES):
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
                parent=scene.find(".//Node[@name='Native 800 pixel scene']")
                parent.remove(parent.find("Node[@name='Park ground']"))
                self.assertEqual(ET.tostring(scene),ET.tostring(expected))

    def test_juniper_stealth_grey_uses_approved_layout(self):
        native=self.scene.find(".//Node[@name='Native 800 pixel scene']")
        for side,x in (('left',240),('right',560)):
            car=native.find(f"Node[@name='{side} blind spot']")
            self.assertEqual(float(car.get('x')),x)
            self.assertEqual(float(car.get('y')),292)
            for image in car.iter('Image'):
                self.assertGreater(float(image.get('scaleX','1')),0)
                self.assertEqual(float(image.get('rotation','0')),0)
            placement=car.find(f".//Node[@name='{side} projected lane placement']")
            self.assertGreater(float(placement.get('scaleY')),0)
            self.assertEqual(math.copysign(1,float(placement.get('scaleX'))),-1 if side=='right' else 1)
        ego=native.find("Node[@name='Driving ego vehicle view selector']")
        from myj_projection import EGO_CHASE_Y, EGO_CHASE_SCALE, CONTACT_Y
        self.assertEqual(float(ego.get('x')),400)
        self.assertAlmostEqual(float(ego.get('y')),EGO_CHASE_Y)
        self.assertAlmostEqual(float(ego.get('scaleX')),EGO_CHASE_SCALE)
        self.assertAlmostEqual(float(ego.get('y'))+(1003-599.5)*EGO_CHASE_SCALE,CONTACT_Y)
        assets=vehicle_assets(VEHICLES[0])
        for color in ('grey','red'):
            self.assertEqual(assets['left_'+color],assets['right_'+color])
            self.assertIn('model-y-juniper-stealth-grey/blind-spot-',assets['left_'+color])

    def test_other_juniper_variants_retain_their_existing_template(self):
        def template(vehicle):
            scene = Scene(vehicle).build()
            for asset in scene.iter('ImageAsset'):
                if asset.get('name') in ('ego', 'park'):
                    asset.set('file', ASSETS[asset.get('name')])
            native = scene.find(".//Node[@name='Native 800 pixel scene']")
            native.remove(native.find("Node[@name='Park ground']"))
            return ET.tostring(scene)
        expected = template('model-y-juniper-white-multi-coat')
        for vehicle in (v for v in JUNIPER_VEHICLES if v != VEHICLES[0]):
            with self.subTest(vehicle=vehicle):
                self.assertEqual(template(vehicle), expected)
                self.assertEqual(vehicle_assets(vehicle)['ego'], f'assets/vehicle/{vehicle}/drive.png')
                self.assertEqual(vehicle_assets(vehicle)['park'], f'assets/vehicle/{vehicle}/park.png')

    def test_unknown_vehicle_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'Unsupported vehicle'):
            Scene('../unknown')

    def test_all_highland_paint_variants_are_registered(self):
        for color in ('stealth-grey','pearl-white-multi-coat','marine-blue',
                      'diamond-black','ultra-red','quicksilver'):
            self.assertIn('model-3-highland-'+color,VEHICLES)

    def test_legacy_model_y_is_a_separate_vehicle_with_its_own_assets(self):
        vehicle='model-y-legacy-deep-blue-metallic'
        self.assertIn(vehicle,VEHICLES)
        assets=vehicle_assets(vehicle)
        for name in ('ego','park'):
            view='drive' if name=='ego' else 'park'
            self.assertEqual(assets[name],f'assets/vehicle/{vehicle}/{view}.png')
            self.assertNotEqual(assets[name],ASSETS[name])
        self.assertEqual({key:path for key,path in assets.items() if key not in ('ego','park')},
                         {key:path for key,path in ASSETS.items() if key not in ('ego','park')})
        for view,dimensions in (('park',(410,307)),('drive',(122,136))):
            data=(ROOT/f'assets/vehicle/{vehicle}/{view}.png').read_bytes()
            self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n')
            self.assertEqual((int.from_bytes(data[16:20],'big'),int.from_bytes(data[20:24],'big')),dimensions)
            self.assertEqual(data[25],6,'Vehicle sprites must retain RGBA alpha')

    def test_legacy_paint_variants_have_dedicated_assets_and_matching_ground(self):
        from park_ground import park_ground_outline
        for paint in ('pearl-white-multi-coat','midnight-silver-metallic'):
            vehicle='model-y-legacy-'+paint
            with self.subTest(vehicle=vehicle):
                self.assertIn(vehicle,VEHICLES)
                for role,view,width,height in (('park','park',410,307),('ego','drive',122,136)):
                    path=vehicle_assets(vehicle)[role]
                    self.assertEqual(path,f'assets/vehicle/{vehicle}/{view}.png')
                    data=(ROOT/path).read_bytes()
                    self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n')
                    self.assertEqual((int.from_bytes(data[16:20],'big'),int.from_bytes(data[20:24],'big')),
                                     (width,height))
                    self.assertEqual(data[25],6,'Vehicle sprites must retain RGBA alpha')
                self.assertEqual(park_ground_outline(vehicle),
                                 park_ground_outline('model-y-legacy-deep-blue-metallic'))

    def test_turn_signals_are_original_mirrored_vectors(self):
        left=turn_signal_points('left')
        self.assertEqual(turn_signal_points('right'),[(-x,y) for x,y in left])
        for side,x in (('left',300),('right',500)):
            with self.subTest(side=side):
                arrow=self.scene.find(f".//Node[@name='{side} turn signal']")
                self.assertEqual((arrow.get('x'),arrow.get('y')),(str(x),'42'))
                self.assertEqual(list(arrow.iter('Image')),[])
                path=arrow.find('Shape/PointsPath')
                self.assertEqual(path.get('isClosed'),'true')
                points=[(float(v.get('x')),float(v.get('y'))) for v in path]
                self.assertEqual(points,turn_signal_points(side))
                self.assertTrue(all(v.get('radius')=='1.2' for v in path))
                self.assertEqual(arrow.find('Shape/Fill/SolidColor').get('colorValue'),'FF35D774')
                self.assertEqual(arrow.find('DataBindContext').get('sourcePathIds'),
                                 f'1:1-{IDS[side+"Blinker"]}')
        for name in ('turn-left.png','turn-right.png'):
            self.assertFalse((ROOT/'assets'/name).exists())
        self.assertFalse(any(key.startswith('turn_') for key in ASSETS))

    def test_generic_vehicle_has_dedicated_rgba_assets(self):
        self.assertIn('generic-vehicle',VEHICLES)
        assets=vehicle_assets('generic-vehicle')
        for name,view,size in (('ego','drive',(111,124)),('park','park',(410,307))):
            self.assertEqual(assets[name],f'assets/vehicle/generic-vehicle/{view}.png')
            data=(ROOT/assets[name]).read_bytes()
            self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n')
            self.assertEqual((int.from_bytes(data[16:20],'big'),int.from_bytes(data[20:24],'big')),size)
            self.assertEqual(data[25],6)

    def test_vector_turn_signal_keeps_off_dim_bright_states(self):
        for side in ('left','right'):
            for state,opacity in ((0,0),(1,.5),(2,1)):
                with self.subTest(side=side,state=state):
                    result=eval(FORMULAS[side+' Arrow'],{'__builtins__':{}},
                                dict(input=state,max=max,min=min,sqrt=math.sqrt,pow=pow))
                    self.assertEqual(result,opacity)

    def test_turn_signal_has_shorter_shaft_and_larger_triangle(self):
        tip, head_top, neck_top, tail_top, *_ = turn_signal_points('left')
        self.assertEqual(tail_top[0] - neck_top[0], 9)
        self.assertEqual(head_top[0] - tip[0], 23)
        self.assertEqual(abs(head_top[1]) * 2, 36)
        self.assertEqual(neck_top[1], -7)
        self.assertEqual(abs(tail_top[1]) * 2, 14)

    def test_cruise_set_speed_visibility_and_inter_font(self):
        self.assertEqual(PROPERTIES['accSetSpeed'][0], 'Number')
        self.assertEqual(PROPERTIES['selfdriveActive'], ('Boolean', False))
        self.assertIsNone(self.scene.find(".//StateMachineLayer[@name='Cruise assist visibility']"))
        cruise = self.scene.find(".//Node[@name='Cruise set speed']")
        anchor=self.scene.find(".//Node[@name='Cruise anchor']")
        self.assertEqual(anchor.get('x'), '-108')
        self.assertIsNone(anchor.get('opacity'))
        self.assertEqual(anchor.findall('DataBindContext'),[])
        binding = cruise.find('DataBindContext')
        self.assertEqual(binding.get('sourcePathIds'), f"1:1-{IDS['accSetSpeed']}")
        self.assertEqual(binding.get('propertyKey'),'18')
        mapper=self.scene.find(f"DataConverterRangeMapper[@id='{binding.get('converterId')}']")
        self.assertIsNotNone(mapper)
        self.assertEqual([mapper.get(k) for k in ('minInput','maxInput','minOutput','maxOutput')],['0','1','0','1'])
        self.assertEqual([mapper.get(k) for k in ('clampLower','clampUpper')],['true','true'])
        self.assertFalse(any(obj.get('objectId') in (anchor.get('id'),cruise.get('id'))
                             for obj in self.scene.iter('KeyedObject')))
        value = cruise.find("Text[@name='Cruise speed value']")
        style = value.find('TextStylePaint')
        self.assertEqual(style.get('fontAssetId'), '2:900')
        self.assertEqual(style.get('styleName'), 'Regular')
        self.assertEqual(value.find('TextValueRun/DataBindContext').get('sourcePathIds'),
                         f"1:1-{IDS['accSetSpeed']}")
        self.assertEqual(style.get('familyName'), 'Inter')
        caption=cruise.find("Text[@name='Cruise MAX label']")
        bindings=caption.findall('TextStylePaint/Fill/SolidColor/DataBindContext')
        self.assertEqual({b.get('propertyKey') for b in bindings},{'118','136','210'})
        self.assertTrue(all(b.get('sourcePathIds')==f"1:1-{IDS['adasOn']}" for b in bindings))

    def test_approved_inter_weights_are_used_consistently(self):
        expected={'Current speed':('2:900','Regular'), 'Cruise speed value':('2:900','Regular'),
                  'Speed limit value':('2:901','SemiBold'), 'Cruise MAX label':('2:901','SemiBold'),
                  'Current speed mph':('2:900','Regular'), 'Gear D':('2:902','Medium'),
                  'Battery percentage':('2:902','Medium')}
        for name,(identity,weight) in expected.items():
            style=self.scene.find(f".//Text[@name='{name}']/TextStylePaint")
            self.assertEqual((style.get('fontAssetId'),style.get('styleName')),(identity,weight))
            self.assertEqual(style.get('familyName'),'Inter')
        self.assertEqual({a.get('file') for a in self.scene.iter('FontAsset')},
                         {'fonts/Inter-Regular.ttf','fonts/Inter-Medium.ttf','fonts/Inter-SemiBold.ttf'})

    def test_speed_unit_is_shaped_inline_without_digit_count_offsets(self):
        cluster=self.scene.find(".//Node[@name='Speed and power']")
        for name,label in (('Current speed','km/h'),('Current speed mph','mph')):
            text=cluster.find(f"Text[@name='{name}']")
            self.assertEqual((text.get('x'),text.get('y'),text.get('width')),('20','23','300'))
            runs=text.findall('TextValueRun')
            self.assertEqual(len(runs),2)
            self.assertEqual(runs[1].get('text'),'\u2009'+label)
            style=text.find(f"TextStylePaint[@id='{runs[1].get('styleId')}']")
            self.assertEqual((style.get('fontAssetId'),style.get('fontSize')),('2:902','21.25'))
            self.assertEqual(style.find('Fill/SolidColor').get('colorValue'),'FFB8C1C5')
            self.assertIsNotNone(text.find('DataBindContext'))
            self.assertEqual(text.findall("DataBindContext[@propertyKey='13']"),[])
        self.assertIsNone(self.scene.find("DataConverterFormula[@name='Unit position']"))

    def test_device_battery_widgets_and_phone_bindings(self):
        car=self.scene.find(".//Node[@name='Known battery']")
        self.assertIsNone(car.find("Node[@name='Car battery device icon']"))
        self.assertEqual(car.get('x'),'54')
        phone_setting=self.scene.find(".//Node[@name='Phone battery setting']")
        self.assertIsNotNone(self.scene.find(".//LayoutComponent[@name='Gear anchor']/Node[@name='Phone battery setting']"))
        self.assertEqual(phone_setting.get('x'),'-270')
        self.assertIsNone(car.find(".//Shape[@name='Car side silhouette']"))
        setting=phone_setting.find('DataBindContext')
        self.assertEqual(setting.get('sourcePathIds'),f"1:1-{IDS['showPhoneBattery']}")
        self.assertEqual(setting.get('converterId'),'2:3')
        phone=phone_setting.find("Node[@name='Known phone battery']")
        self.assertIsNotNone(phone.find("Node[@name='Phone battery device icon']"))
        self.assertEqual(phone.find('DataBindContext').get('sourcePathIds'),f"1:1-{IDS['phoneBattery']}")
        value=phone.find(".//Text[@name='Phone battery percentage']/TextValueRun/DataBindContext")
        self.assertEqual(value.get('sourcePathIds'),f"1:1-{IDS['phoneBattery']}")
        for number,percent,known in ((-1,0,0),(0,0,1),(9,9,1),(78,78,1),(99.9,99,1),(100,100,1),(150,100,1)):
            env=dict(input=number,min=min,max=max,floor=math.floor)
            self.assertEqual(eval(FORMULAS['Phone Battery Percent'],{'__builtins__':{}},env),percent)
            self.assertEqual(eval(FORMULAS['Phone Battery Known'],{'__builtins__':{}},env),known)

    def test_power_rail_uses_responsive_footer_artboard(self):
        cluster=self.scene.find("Artboard[@name='Footer power bar']")
        for name in ('Consumption fill','Recuperation fill','Power track'):
            shape=cluster.find(f"Shape[@name='{name}']")
            self.assertEqual(shape.get('x'),'450')
            rectangle=shape.find('Rectangle')
            self.assertEqual(rectangle.get('height'),'14.4')
        slot=self.scene.find(".//LayoutComponent[@name='Bottom power bar slot']")
        self.assertIsNotNone(slot)
        self.assertEqual(slot.get('width'),'50')

    def test_car_and_phone_battery_percentages_have_matching_typography(self):
        for car_name,phone_name in (('Battery percentage','Phone battery percentage'),
                                    ('Percent sign','Phone percent sign')):
            car=self.scene.find(f".//Text[@name='{car_name}']/TextStylePaint")
            phone=self.scene.find(f".//Text[@name='{phone_name}']/TextStylePaint")
            for key in ('fontSize','fontAssetId','familyName','styleName'):
                self.assertEqual(car.get(key),phone.get(key))
            self.assertEqual(phone.get('fontSize'),'18')

    def test_odometer_has_inline_muted_km_suffix_and_live_host_bindings(self):
        setting=self.scene.find(".//Node[@name='Odometer setting']")
        self.assertEqual(setting.get('x'),'324')
        self.assertEqual(setting.find('DataBindContext').get('sourcePathIds'),
                         f"1:1-{IDS['showOdometer']}")
        for name in ('Metric','Imperial'):
            for count in range(1,5):
                text=setting.find(f".//Text[@name='{name} odometer {count} groups']")
                runs=text.findall('TextValueRun')
                self.assertEqual(len(runs),count*2)
                self.assertEqual(runs[-1].get('text'),'km')
                self.assertEqual([r.get('text') for r in runs if r.get('name')=='Thousands separator'],
                                 ['.']*(count-1))
                self.assertEqual(runs[0].find('DataBindContext').get('sourcePathIds'),
                                 f"1:1-{IDS['odometer']}")
                style=text.find(f"TextStylePaint[@id='{runs[-1].get('styleId')}']")
                self.assertEqual(style.find('Fill/SolidColor').get('colorValue'),'FF7C8589')
        pad=self.scene.find("DataConverterStringPad[@name='Odometer three digits']")
        self.assertEqual((pad.get('text'),pad.get('length')),('0','3'))
        for value,expected in ((0,0),(12345.9,12345),(999999,999999)):
            self.assertEqual(eval(FORMULAS['Odometer Km'],{'__builtins__':{}},
                                  dict(input=value,max=max,floor=math.floor)),expected)
        self.assertEqual(eval(FORMULAS['Odometer Imperial To Km'],{'__builtins__':{}},
                              dict(input=1000,max=max,floor=math.floor)),1609)

    def test_autopilot_uses_flat_host_compatible_boolean_binding(self):
        self.assertEqual(PROPERTIES['adasOn'][0], 'Boolean')
        for selector in (".//Image[@name='Autopilot']", ".//Node[@name='Assist lanes']"):
            binding = self.scene.find(selector + '/DataBindContext')
            self.assertEqual(binding.attrib, dict(sourcePathIds=f"1:1-{IDS['adasOn']}",
                                                 propertyKey='18', converterId='2:3'))
        converter = self.scene.find("DataConverterGroup[@id='2:3']")
        self.assertEqual([item.get('converterId') for item in converter], ['2:2', '2:4'])
        self.assertIsNotNone(self.scene.find("DataConverterToString[@id='2:2']"))
        self.assertIsNotNone(self.scene.find("DataConverterToNumber[@id='2:4']"))
        self.assertIsNone(self.scene.find("DataConverterFormula[@name='Assist active']"))

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

    def test_speed_readouts_keep_the_approved_optical_alignment(self):
        speed=self.scene.find(".//Text[@name='Current speed']")
        limit=self.scene.find(".//Node[@name='Known speed limit']")
        cruise=self.scene.find(".//Node[@name='Cruise anchor']")
        self.assertEqual((speed.get('x'),speed.get('y')),('20','23'))
        self.assertEqual(limit.get('y'),'181')
        self.assertEqual(cruise.get('y'),'174.5')

    def test_generated_source_is_reproducible(self):
        ET.indent(self.scene, space='  ')
        self.assertEqual((ROOT/'scene.rml').read_text(encoding='utf-8'),
                         ET.tostring(self.scene, encoding='unicode') + '\n')

    def test_no_vehicle_transition_or_intermediate_assets_are_shipped(self):
        main = self.scene.find("Artboard[@name='Newhaven']")
        animated_ids={n.get('id') for n in main.iter() if n.get('id')}
        self.assertTrue(all(obj.get('objectId') in animated_ids for obj in main.iter('KeyedObject')))
        self.assertEqual(list(self.scene.iter('ListenerViewModelChange')),[])
        from vehicle_angles import POSE_ASSETS
        self.assertEqual(len(list(self.scene.iter('ImageAsset'))),len(ASSETS)+len(POSE_ASSETS))
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
            if name=='Driving ego vehicle':
                image=self.scene.find(".//Node[@name='Driving ego vehicle view selector']")
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
        power=self.scene.find(".//NestedArtboardLeaf[@name='Footer power and regeneration']")
        self.assertIsNotNone(power.find("DataBindContext[@propertyKey='18']"))

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
        self.assertEqual(len(road.findall('.//Shape')),128)
        clock=road.find("Node[@name='Road phase clock']")
        self.assertEqual(animation.find('KeyedObject').get('objectId'),clock.get('id'))
        keys=animation.findall("KeyedObject/KeyedProperty[@propertyKey='13']/KeyFrameDouble")
        self.assertEqual([(k.get('frame'),k.get('value')) for k in keys],[('0','0'),('60','1')])
        for stroke in road.iter('Stroke'):
            binding=stroke.find("DataBindContext[@propertyKey='47']")
            self.assertEqual(binding.get('sourcePathIds'),f"1:1-{IDS['_roadPhase']}")
        from myj_projection import HORIZON, FOCAL, DEPTH_SCALE, PAINT_LENGTH, FAR_Z
        for shape in road.iter('Shape'):
            vertices=shape.findall('PointsPath/StraightVertex')
            self.assertEqual(len(vertices),4)
            near,far=vertices[:2]
            zn=DEPTH_SCALE/(float(near.get('y'))-HORIZON)
            zf=DEPTH_SCALE/(float(far.get('y'))-HORIZON)
            self.assertAlmostEqual(zf-zn,min(PAINT_LENGTH,FAR_Z-zn))
            self.assertAlmostEqual((float(near.get('x'))-400)*zn/FOCAL,
                                   (float(far.get('x'))-400)*zf/FOCAL)

    def test_steering_has_signed_dead_zone_and_bounded_monotonic_curve(self):
        self.assertEqual(PROPERTIES['egoSteeringAngle'],('Number',0))
        self.assertEqual(PROPERTIES['_roadBend'],('Number',0))
        def bend(angle):
            return eval(ROAD_BEND,{'__builtins__':{}},dict(input=angle,min=min,max=max))
        for angle in (-2,-1,0,1,2):
            self.assertEqual(bend(angle),0)
        for angle in (3,15,30,60,90,180,819):
            self.assertGreater(bend(angle),0)
            self.assertLessEqual(bend(angle),1)
            self.assertEqual(bend(-angle),-bend(angle))
        self.assertEqual(bend(90),bend(819))
        self.assertEqual(sorted(bend(n) for n in range(-180,181)),
                         [bend(n) for n in range(-180,181)])

    def test_native_steering_smoothing_is_separate_from_road_travel(self):
        road=self.scene.find("Artboard[@name='Road motion']")
        steering=road.find("Node[@name='Smoothed road steering']")
        bindings=steering.findall('DataBindContext')
        self.assertEqual(bindings[0].get('sourcePathIds'),f"1:1-{IDS['egoSteeringAngle']}")
        self.assertEqual(bindings[1].get('sourcePathIds'),f"1:1-{IDS['_roadBend']}")
        self.assertEqual(bindings[1].get('direction'),'true')
        smoothing=self.scene.find("DataConverterInterpolator[@name='Road steering smoothing']")
        self.assertEqual(float(smoothing.get('duration')),ROAD_STEERING_SMOOTHING)
        self.assertEqual(ROAD_STEERING_SMOOTHING,.12)
        clock=road.find("Node[@name='Road phase clock']/DataBindContext")
        self.assertEqual(clock.get('sourcePathIds'),f"1:1-{IDS['_roadPhase']}")
        self.assertEqual(clock.get('direction'),'true')

    def test_curved_lane_geometry_keeps_near_road_anchored(self):
        road=self.scene.find("Artboard[@name='Road motion']")
        for shape in road.iter('Shape'):
            vertices=shape.findall('PointsPath/StraightVertex')
            self.assertEqual(len(vertices),4)
            for vertex in vertices:
                self.assertEqual(vertex.get('radius'),'0')
                self.assertEqual({b.get('propertyKey') for b in vertex.findall('DataBindContext')},
                                 {'24','25'})
        self.assertEqual(ROAD_BEND_ANCHOR,240)
        for bend in (-1,0,1):
            shifts=[ROAD_BEND_PIXELS*bend*max(0,1-y/ROAD_BEND_ANCHOR)**2
                    for y in (0,120,240,300,384)]
            self.assertEqual(shifts,[95*bend,23.75*bend,0,0,0])

    def test_rejected_motion_interpolation_is_not_shipped(self):
        motion = [a for a in self.scene.iter('ImageAsset') if '/motion/' in a.get('file','')]
        self.assertEqual(motion,[])

    def test_projected_blind_spots_have_no_fabricated_relative_motion(self):
        main=self.scene.find("Artboard[@name='Newhaven']")
        from myj_projection import ADJACENT_CONTACT_Y, CONTACT_Y, ADJACENT_LATERAL_OFFSET
        self.assertGreater(ADJACENT_CONTACT_Y, CONTACT_Y)
        self.assertEqual(ADJACENT_LATERAL_OFFSET,3.2)
        for side in ('left','right'):
            self.assertIsNone(main.find(f"StateMachine/StateMachineLayer[@name='{side} independent car motion']"))
            arrival=main.find(f".//Node[@name='{side} blind spot arrival']")
            self.assertEqual((arrival.get('x'),arrival.get('y')),('0','0'))
            for state in ('hidden','visible','exiting'):
                animation=main.find(f"LinearAnimation[@name='{side} arrival {state}']")
                self.assertEqual({p.get('propertyKey') for p in animation.iter('KeyedProperty')},{'18'})
            placement=arrival.find(f".//Node[@name='{side} projected lane placement']")
            self.assertIsNotNone(placement.find(f"Node[@name='{side} attached tire and chassis occlusion']"))
        ground=main.find(".//Node[@name='Driving tire and chassis contact']")
        self.assertIsNotNone(ground.find("DataBindContext[@propertyKey='18']"))

    def test_outer_boundaries_follow_each_sides_blind_spot_visibility(self):
        road=self.scene.find("Artboard[@name='Road motion']")
        for side in ('left','right'):
            boundary=road.find(f".//Node[@name='{side} occupied outer boundary']")
            self.assertEqual(len(boundary.findall('Shape')),16)
            binding=boundary.find("DataBindContext[@propertyKey='18']")
            self.assertEqual(binding.get('sourcePathIds'),f"1:1-{IDS[side+'BlindSpot']}")
            expression=FORMULAS[side+' Occupied']
            for occupied,monitor,blinker,gear,expected in (
                (0,True,0,4,0),(1,True,0,4,1),(1,False,0,4,0),
                (1,False,2,4,1),(1,True,0,1,0)):
                values=dict(min=min,max=max,sqrt=math.sqrt,pow=pow,gear=gear,alwaysOnBlindSpotMonitor=monitor)
                values.update({side+'BlindSpot':occupied,side+'Blinker':blinker})
                self.assertEqual(eval(expression,{'__builtins__':{}},values),expected)

    def test_adjacent_rear_contacts_and_inner_flanks_are_mirrored_about_vanishing_point(self):
        from myj_projection import FOCAL, LANE_WIDTH, CONTACT_Z, ADJACENT_LATERAL_OFFSET, ADJACENT_Z
        self.assertAlmostEqual(FOCAL*LANE_WIDTH/CONTACT_Z/109,1.7)
        native=self.scene.find(".//Node[@name='Native 800 pixel scene']")
        rear_x=(-80.41935483870968+47.44736842105263)/2
        contacts=[]
        for side,sign in (('left',-1),('right',1)):
            car=native.find(f"Node[@name='{side} blind spot']")
            placement=car.find(f".//Node[@name='{side} projected lane placement']")
            scale=float(placement.get('scaleX'))
            contact=float(car.get('x'))+float(placement.get('x'))+rear_x*scale
            self.assertAlmostEqual(contact,400+sign*FOCAL*ADJACENT_LATERAL_OFFSET/ADJACENT_Z)
            contacts.append(contact)
            self.assertEqual(math.copysign(1,scale),-sign)
            self.assertEqual(float(placement.find('Node').get('scaleX','1')),1)
        self.assertAlmostEqual(sum(contacts),800)

    def test_ground_curvature_is_continuous_and_moves_the_distant_vanishing_point(self):
        from myj_projection import (ground_curve,ground_curve_expression,CONTACT_Z,FOCAL,
                                    CURVE_HEADING,CURVE_ACCELERATION,CURVE_TRANSITION)
        limit=FOCAL*(CURVE_HEADING+.5*CURVE_ACCELERATION*CURVE_TRANSITION)
        self.assertGreater(limit,0)
        for bend in (-1,-.5,0,.5,1):
            self.assertEqual(ground_curve(CONTACT_Z,bend),0)
            for z in (6,CONTACT_Z,30,CONTACT_Z+CURVE_TRANSITION,186,1e8):
                expression=ground_curve_expression(str(z),'input')
                self.assertAlmostEqual(eval(expression,{'__builtins__':{}},
                                            dict(input=bend,min=min,max=max,pow=pow)),
                                       ground_curve(z,bend))
                self.assertAlmostEqual(ground_curve(z,-bend),-ground_curve(z,bend))
            join=CONTACT_Z+CURVE_TRANSITION
            eps=1e-5
            before=(ground_curve(join,bend)-ground_curve(join-eps,bend))/eps
            after=(ground_curve(join+eps,bend)-ground_curve(join,bend))/eps
            self.assertAlmostEqual(before,after,places=7)
            self.assertAlmostEqual(FOCAL*ground_curve(1e8,bend)/1e8,bend*limit,places=3)

    def test_curved_vehicle_anchors_replace_legacy_screen_translation(self):
        native=self.scene.find(".//Node[@name='Native 800 pixel scene']")
        for side in ('left','right'):
            car=native.find(f"Node[@name='{side} blind spot']")
            self.assertIsNone(car.find("DataBindContext[@propertyKey='13']"))
            placement=car.find(f".//Node[@name='{side} projected lane placement']")
            self.assertIsNotNone(placement.find("DataBindContext[@propertyKey='13']"))
            for image in car.iter('Image'):
                self.assertIsNone(image.find("DataBindContext[@propertyKey='15']"))
                self.assertEqual(image.get('rotation'),'0')
        road=native.find("NestedArtboard[@name='Speed driven road']")
        self.assertIsNone(road.find("DataBindContext[@propertyKey='13']"))
        ego=native.find("Node[@name='Driving ego vehicle view selector']")
        self.assertEqual(len(ego.findall('Solo/Image')),3)
        for image in ego.findall('Solo/Image'):
            self.assertIsNone(image.find("DataBindContext[@propertyKey='15']"))

    def test_vehicle_shadows_share_heading_and_adjacent_lane_radii_are_mirrored(self):
        from myj_projection import lane_frame_expressions,ADJACENT_Z,ADJACENT_LATERAL_OFFSET
        def evaluate(expression,bend):
            return eval(expression,{'__builtins__':{}},
                        dict(input=bend,min=min,max=max,pow=pow,sqrt=math.sqrt))
        left=lane_frame_expressions(str(ADJACENT_Z),-ADJACENT_LATERAL_OFFSET,'input')
        right=lane_frame_expressions(str(ADJACENT_Z),ADJACENT_LATERAL_OFFSET,'input')
        for bend in (-1,-.5,0,.5,1):
            self.assertAlmostEqual(evaluate(left[0],bend),-evaluate(right[0],-bend))
            self.assertAlmostEqual(evaluate(left[1],bend),evaluate(right[1],-bend))
            self.assertGreater(evaluate(left[1],bend),0)
        self.assertNotEqual(evaluate(left[1],1),evaluate(right[1],1))
        native=self.scene.find(".//Node[@name='Native 800 pixel scene']")
        shadows=[n for n in native.iter('Node') if n.get('name')=='Driving tire and chassis contact'
                 or 'attached tire and chassis occlusion' in n.get('name','')]
        self.assertEqual(len(shadows),3)
        for shadow in shadows:
            self.assertEqual(float(shadow.get('rotation','0')),0)
            self.assertIsNone(shadow.find("DataBindContext[@propertyKey='15']"))
        selectors=[n for n in native.iter('Node') if n.get('name','').endswith(' view selector')]
        self.assertEqual(len(selectors),5)
        for selector in selectors:
            images=selector.findall('Solo/Image')
            self.assertEqual(len(images),3)
            for image in images:
                self.assertEqual(float(image.get('rotation','0')),0)
                self.assertIsNone(image.find("DataBindContext[@propertyKey='15']"))
                self.assertIsNone(image.find("DataBindContext[@propertyKey='18']"))
        ego=native.find("Node[@name='Driving ego vehicle view selector']")
        positive=ego.find("Solo/Image[@name='Driving ego vehicle actual angle 1']")
        negative=ego.find("Solo/Image[@name='Driving ego vehicle actual angle -1']")
        self.assertLess(float(positive.get('scaleX')),0)
        self.assertGreater(float(negative.get('scaleX')),0)
        from vehicle_angles import EGO_BODY_HEIGHT,ASSET_DIR
        geometry=json.loads((ROOT/ASSET_DIR/'geometry.json').read_text())['ego']
        (_,height),box,_=geometry
        self.assertEqual(EGO_BODY_HEIGHT,875)
        for image in (positive,negative):
            scale=float(image.get('scaleY'))
            self.assertAlmostEqual((box[3]-box[1])*scale,EGO_BODY_HEIGHT)
            self.assertAlmostEqual(float(image.get('y'))+(box[3]-1-height/2)*scale,403.5)
            self.assertAlmostEqual(abs(float(image.get('scaleX'))),scale)


    def test_horizon_tracks_turn_direction_without_a_far_field_trajectory_switch(self):
        from myj_projection import (ground_curve,ground_slope_expression,vanishing_point_x,
                                    CONTACT_Z,FOCAL,CURVE_TRANSITION)
        for bend in (-1,-.5,.5,1):
            self.assertGreater((vanishing_point_x(bend)-400)*bend,0)
            samples=[CONTACT_Z+i*2 for i in range(300)]
            signed=[FOCAL*ground_curve(z,bend)/z*bend for z in samples]
            self.assertEqual(signed,sorted(signed))
            self.assertTrue(all(x<=(vanishing_point_x(bend)-400)*bend for x in signed))
            for z in (6,CONTACT_Z,CONTACT_Z+CURVE_TRANSITION,186,600):
                eps=1e-4
                derivative=(ground_curve(z+eps,bend)-ground_curve(z-eps,bend))/(2*eps)
                analytic=eval(ground_slope_expression(str(z),'input'),
                              {'__builtins__':{}},dict(input=bend,max=max,pow=pow))
                self.assertAlmostEqual(derivative,analytic,places=6)
            join=CONTACT_Z+CURVE_TRANSITION
            def curvature(z):
                h=.01
                return (ground_curve(z+h,bend)-2*ground_curve(z,bend)+ground_curve(z-h,bend))/(h*h)
            self.assertAlmostEqual(curvature(join-.01),curvature(join+.01),places=6)

    def test_amplified_curve_has_twenty_percent_horizon_range_and_five_degree_ego_heading(self):
        from myj_projection import (vanishing_point_x,lane_heading_expression,CONTACT_Z,
                                    CURVE_ACCELERATION,MAX_VEHICLE_HEADING)
        self.assertEqual(CURVE_ACCELERATION,.0024)
        for bend in (-1,0,1):
            self.assertAlmostEqual(vanishing_point_x(bend),400+160*bend)
            expression=lane_heading_expression(CONTACT_Z,0)
            heading=eval(expression,{'__builtins__':{}},dict(input=bend,min=min,max=max,pow=pow))
            self.assertAlmostEqual(math.degrees(heading),5*bend)
            self.assertLessEqual(abs(heading),MAX_VEHICLE_HEADING)

    def test_road_texture_motion_is_bounded_and_settles_at_rest(self):
        from road_dynamics import dynamics_expressions,DESIGN_SCALE
        from myj_projection import EGO_CHASE_Y
        expressions=dynamics_expressions(EGO_CHASE_Y)
        def values(speed,phase,gear=4,imperial=0):
            variables=dict(egoSpeed=speed,_roadPhase=phase,gear=gear,input=imperial,
                           min=min,max=max,pow=pow,sqrt=math.sqrt,sin=math.sin)
            return {k:eval(v,{'__builtins__':{}},variables) for k,v in expressions.items()}
        for speed in (0,25,100,200):
            for gear in (1,2,3,4):
                for step in range(61):
                    v=values(speed,step/60,gear)
                    self.assertLessEqual(abs((v['body_y']-EGO_CHASE_Y)*DESIGN_SCALE),.5+1e-9)
                    if speed==0 or gear in (1,3):
                        self.assertEqual(v,dict(body_y=EGO_CHASE_Y))
        for phase in (0,.13,.27,.81,1):
            a,b=values(60,phase,imperial=1),values(60*1.609344,phase)
            for key in a:
                self.assertAlmostEqual(a[key],b[key])
        a,b=values(100,0),values(100,1)
        for key in a:
            self.assertAlmostEqual(a[key],b[key])
        native=self.scene.find(".//Node[@name='Native 800 pixel scene']")
        ego=native.find("Node[@name='Driving ego vehicle view selector']")
        self.assertIsNone(ego.find("DataBindContext[@propertyKey='14']"))
        self.assertIsNone(native.find(".//Node[@name='Ground anchored tire pressure']"))
        for side in ('left','right'):
            vibration=native.find(f".//Node[@name='{side} road vibration']")
            self.assertIsNotNone(vibration.find("DataBindContext[@propertyKey='14']"))
            self.assertEqual(len(vibration.findall('Node')),2)
            self.assertTrue(all(n.get('name','').endswith(' vehicle view selector') for n in vibration.findall('Node')))
    def test_pose_selection_is_exclusive_above_50_degrees_with_zero_crossfade(self):
        from vehicle_angles import select_pose
        main=self.scene.find("Artboard[@name='Newhaven']")
        solos=[s for s in main.iter('Solo') if s.get('name','').endswith(' exclusive poses')]
        self.assertEqual(len(solos),5)
        layers=[l for l in main.findall('StateMachine/StateMachineLayer')
                if l.get('name','').endswith(' exclusive pose')]
        self.assertEqual(len(layers),5)
        animations={a.get('id'):a for a in main.findall('LinearAnimation')}
        operators={'greaterThanOrEqual':lambda x,y:x>=y,'greaterThan':lambda x,y:x>y,
                   'lessThanOrEqual':lambda x,y:x<=y,'lessThan':lambda x,y:x<y}
        all_pose_ids={im.get('id') for solo in solos for im in solo.findall('Image')}
        for solo in solos:
            self.assertEqual(len(solo.findall('Image')),3)
            self.assertIn(solo.get('activeComponentId'),{im.get('id') for im in solo.findall('Image')})
            self.assertTrue(all(im.find("DataBindContext[@propertyKey='18']") is None for im in solo.findall('Image')))
        for layer in layers:
            states=layer.findall('AnimationState')
            pose={state.get('id'):int(animations[state.get('animationId')].get('name').split()[-1]) for state in states}
            for state in states:
                animation=animations[state.get('animationId')]
                prop=animation.find('KeyedObject/KeyedProperty')
                self.assertEqual(prop.get('propertyKey'),'296')
                self.assertIn(prop.find('KeyFrameId').get('value'),all_pose_ids)
                for bend in (-90,-50.001,-50,-49.999,0,49.999,50,50.001,90):
                    targets=[]
                    for transition in state.findall('StateTransition'):
                        self.assertEqual(float(transition.get('duration')),0)
                        conditions=transition.findall('TransitionViewModelCondition')
                        if all(operators[c.get('opValue')](bend,float(c.find('TransitionValueNumberComparator').get('value'))) for c in conditions):
                            targets.append(pose[transition.get('stateToId')])
                    self.assertLessEqual(len(targets),1)
                    current=pose[state.get('id')]
                    self.assertEqual(targets[0] if targets else current,select_pose(current,bend))
        pose=0
        for bend,expected in ((49,0),(50,0),(50.001,1),(60,1),(50,0),(-50,0),(-50.001,-1),(-60,-1),(-50,0),(90,1),(-90,-1)):
            pose=select_pose(pose,bend)
            self.assertEqual(pose,expected)


if __name__ == '__main__':
    unittest.main()
