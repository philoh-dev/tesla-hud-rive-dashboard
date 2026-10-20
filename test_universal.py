import unittest
import xml.etree.ElementTree as ET

from generate import VEHICLES, Scene, vehicle_assets, IDS
from universal import (UniversalScene, VEHICLE_PROPERTY, VEHICLE_PROPERTY_ID,
                       FALLBACK_VEHICLE)
from park_ground import park_wheel_contacts, park_ground_outline


class UniversalDashboardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scene=UniversalScene().build()

    def test_string_selector_defaults_to_generic(self):
        model=self.scene.find("ViewModel[@name='DashViewModel']")
        prop=model.find(f"ViewModelPropertyString[@name='{VEHICLE_PROPERTY}']")
        self.assertEqual(prop.get('id'),VEHICLE_PROPERTY_ID)
        value=model.find(f"ViewModelInstance/ViewModelInstanceString[@viewModelPropertyId='{VEHICLE_PROPERTY_ID}']")
        self.assertEqual(value.get('propertyValue'),FALLBACK_VEHICLE)

    def test_every_vehicle_is_embedded_once_and_shared_assets_are_not_duplicated(self):
        assets=list(self.scene.iter('ImageAsset'))
        expected={path for vehicle in VEHICLES for path in vehicle_assets(vehicle).values()}
        self.assertEqual({asset.get('file') for asset in assets},expected)
        self.assertEqual(len(assets),len(expected))
        self.assertEqual(len(assets),len(VEHICLES)*2+5)

    def test_only_two_vehicle_selectors_share_the_gear_gates(self):
        for role,y in (('park','384'),('ego','234')):
            solo=self.scene.find(f".//Solo[@name='Vehicle {role} selector']")
            self.assertEqual((solo.get('x'),solo.get('y')),('400',y))
            children=solo.findall('Image')
            self.assertEqual(len(children),len(VEHICLES))
            self.assertEqual(solo.get('activeComponentId'),children[0].get('id'))
            self.assertIsNotNone(solo.find('DataBindContext'))
            for image in children:
                self.assertEqual((image.get('x'),image.get('y')),('0','0'))
                self.assertEqual(image.findall('DataBindContext'),[])
                self.assertEqual(image.get('samplerFilter'),'bilinear')
                if role=='park':
                    self.assertEqual(image.get('originY'),'1')

    def test_every_pose_keys_artwork_and_ground_solos_with_direct_child_ids(self):
        for vehicle in VEHICLES:
            animation=self.scene.find(f".//LinearAnimation[@name='Vehicle selection {vehicle}']")
            objects=animation.findall('KeyedObject')
            self.assertEqual(len(objects),3)
            for obj in objects:
                solo=self.scene.find(f".//Solo[@id='{obj.get('objectId')}']")
                key=obj.find('KeyedProperty')
                self.assertEqual(key.get('propertyKey'),'296')
                value=key.find('KeyFrameId').get('value')
                child=next((n for n in solo if n.get('id')==value),None)
                self.assertIsNotNone(child)
                self.assertEqual(child.tag,'Node' if solo.get('name')=='Vehicle ground selector' else 'Image')

    def test_exact_known_strings_and_unknown_fallback_have_disjoint_conditions(self):
        layer=self.scene.find(".//StateMachineLayer[@name='Vehicle design selection']")
        transitions=layer.findall('AnyState/StateTransition')
        self.assertEqual(len(transitions),len(VEHICLES))
        known=set(VEHICLES)-{FALLBACK_VEHICLE}
        selected={}
        for transition in transitions:
            conditions=transition.findall('TransitionViewModelCondition')
            for condition in conditions:
                binding=condition.find('TransitionPropertyViewModelComparator/BindablePropertyString/DataBindContext')
                self.assertEqual(binding.get('propertyKey'),'635')
                self.assertEqual(binding.get('sourcePathIds'),f'1:1-{VEHICLE_PROPERTY_ID}')
            if len(conditions)==1:
                condition=conditions[0]
                self.assertEqual(condition.get('opValue'),'equal')
                selected[condition.find('TransitionValueStringComparator').get('value')]=transition.get('stateToId')
            else:
                self.assertEqual({c.find('TransitionValueStringComparator').get('value') for c in conditions},known)
                self.assertTrue(all(c.get('opValue')=='notEqual' for c in conditions))
                self.assertEqual(transition.get('stateToId'),layer.find('EntryState/StateTransition').get('stateToId'))
        self.assertEqual(set(selected),known)

    def test_other_instruments_and_road_are_unchanged(self):
        single=Scene(FALLBACK_VEHICLE).build()
        for tag,name in (('Node','Speed and power'),('Node','Autopilot anchor'),
                         ('Node','Cruise assist visibility'),('Artboard','Road motion'),
                         ('LayoutComponent','Invisible status region 20 percent')):
            expected=single.find(f".//{tag}[@name='{name}']")
            actual=self.scene.find(f".//{tag}[@name='{name}']")
            self.assertIsNotNone(expected,name)
            self.assertEqual(ET.tostring(actual),ET.tostring(expected),name)

    def test_individual_dashboards_do_not_gain_universal_properties(self):
        self.assertIsNone(Scene().build().find(f".//ViewModelPropertyString[@name='{VEHICLE_PROPERTY}']"))

    def test_selector_is_script_free(self):
        self.assertNotIn('<Script',ET.tostring(self.scene,encoding='unicode'))

    def test_park_ground_is_behind_car_and_independently_gear_gated(self):
        parent=self.scene.find(".//Node[@name='Native 800 pixel scene']")
        ground=parent.find("Node[@name='Park ground']")
        park=parent.find("Solo[@name='Vehicle park selector']")
        self.assertGreater(list(parent).index(ground),list(parent).index(park))
        binding=ground.find('DataBindContext')
        self.assertEqual(binding.get('sourcePathIds'),f"1:1-{IDS['gear']}")
        def tokens(node):
            converter=self.scene.find(f"DataConverterFormula[@id='{node.get('converterId')}']")
            return [ET.tostring(token) for token in converter]
        self.assertEqual(tokens(binding),tokens(park.find('DataBindContext')))
        self.assertEqual(ground.findall('.//Image'),[])

    def test_park_ground_uses_one_continuous_theme_gated_footprint(self):
        ground=self.scene.find(".//Node[@name='Park ground']")
        solo=ground.find('Solo')
        self.assertEqual(len(solo.findall('Node')),len(VEHICLES))
        for layer in solo.findall('Node/Node'):
            binding=layer.find('DataBindContext')
            self.assertEqual(binding.get('sourcePathIds'),f"1:1-{IDS['darkMode']}")
            self.assertEqual(layer.findall('.//Ellipse'),[])
            self.assertEqual(layer.findall('.//RadialGradient'),[])
            self.assertEqual(len(layer.findall('Shape')),1)
            shape=layer.find('Shape')
            self.assertEqual(shape.find('PointsPath').get('isClosed'),'true')
            self.assertEqual(shape.find('PointsPath').get('isClockwise'),'true')
            self.assertEqual(len(shape.findall('Fill')),2)
            for fill in shape.findall('Fill'):
                self.assertEqual(fill.get('fillRule'),'clockwise')
                self.assertIsNotNone(fill.find('Feather'))
            stops=shape.findall('Fill/LinearGradient/GradientStop')
            self.assertEqual(stops[0].get('position'),'0')
            self.assertEqual(stops[-1].get('position'),'1')
        for vehicle in VEHICLES:
            single=Scene(vehicle).build()
            solo=single.find(".//Node[@name='Park ground']/Solo")
            self.assertIsNotNone(solo,vehicle)
            self.assertEqual(len(solo.findall('Node')),1)
            self.assertEqual(solo.find('Node').get('name'),vehicle+' ground')
            self.assertEqual(solo.get('activeComponentId'),solo.find('Node').get('id'))

    def test_single_outline_joins_tyres_and_respects_each_designs_perspective(self):
        solo=self.scene.find(".//Solo[@name='Vehicle ground selector']")
        for vehicle in VEHICLES:
            front,rear=park_wheel_contacts(vehicle)
            design=solo.find(f"Node[@name='{vehicle} ground']")
            for theme in ('Dark','Light'):
                layer=design.find(f"Node[@name='{theme} park ground']")
                vertices=layer.findall('Shape/PointsPath/StraightVertex')
                points=[(float(n.get('x')),float(n.get('y'))) for n in vertices]
                self.assertEqual(points,park_ground_outline(vehicle))
                for x,y in (front,rear):
                    self.assertLessEqual(min((px-x)**2+(py-y)**2 for px,py in points),25)
                area=sum(x*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*y
                         for i,(x,y) in enumerate(points))
                self.assertGreater(area,0)


if __name__=='__main__':
    unittest.main()
