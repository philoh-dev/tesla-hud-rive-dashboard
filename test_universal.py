import unittest
import xml.etree.ElementTree as ET

from generate import VEHICLES, Scene, vehicle_assets
from universal import (UniversalScene, VEHICLE_PROPERTY, VEHICLE_PROPERTY_ID,
                       FALLBACK_VEHICLE)


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

    def test_every_pose_keys_both_solos_with_direct_child_ids(self):
        for vehicle in VEHICLES:
            animation=self.scene.find(f".//LinearAnimation[@name='Vehicle selection {vehicle}']")
            objects=animation.findall('KeyedObject')
            self.assertEqual(len(objects),2)
            for obj in objects:
                solo=self.scene.find(f".//Solo[@id='{obj.get('objectId')}']")
                key=obj.find('KeyedProperty')
                self.assertEqual(key.get('propertyKey'),'296')
                value=key.find('KeyFrameId').get('value')
                self.assertIsNotNone(solo.find(f"Image[@id='{value}']"))

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


if __name__=='__main__':
    unittest.main()
