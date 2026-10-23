"""Cached projection preserves physical road geometry at reported speeds."""
import math
import unittest
from generate import Scene,IDS,PROPERTIES
from myj_projection import (NEAR_Z,FAR_Z,CYCLE_LENGTH,PAINT_LENGTH,
                            ground_curve,ground_slope_expression,lane_frame_expressions,
                            LANE_WIDTH,PAINT_WIDTH,FOCAL,HORIZON,DEPTH_SCALE)
from road_projection_cache import (ROWS,SAMPLE_DEFAULTS,sample_name,
                                    projected_corner_expressions)


class RoadProjectionCacheTest(unittest.TestCase):
    def test_cached_projection_matches_direct_ground_projection(self):
        def evaluate(expression,values):
            return eval(expression,{'__builtins__':{}},dict(values,min=min,max=max,
                       sqrt=math.sqrt,pow=pow))
        for speed in (0,73,103):
            for frame in (0,1,17,59,60,120,899):
                phase=(speed/43.2*frame/60)%1
                for bend in (-1,-.5,0,.5,1):
                    for row in range(ROWS):
                        for end in (0,1):
                            z=min(FAR_Z,max(NEAR_Z,NEAR_Z+row*CYCLE_LENGTH+end*PAINT_LENGTH-CYCLE_LENGTH*phase))
                            slope=evaluate(ground_slope_expression('input','_roadBend'),dict(input=z,_roadBend=bend))
                            values={sample_name(row,end,'Center'):ground_curve(z,bend),
                                    sample_name(row,end,'Slope'):slope,
                                    sample_name(row,end,'InvNormal'):1/math.sqrt(1+slope*slope),
                                    'input':z}
                            for boundary in (1,3):
                                for side in (-1,1):
                                    for edge in (-.5,.5):
                                        offset=side*LANE_WIDTH/2*boundary+edge*PAINT_WIDTH
                                        x,z_world=lane_frame_expressions('input',offset)
                                        original=dict(input=z,_roadBend=bend)
                                        depth=evaluate(z_world,original)
                                        expected=(400+FOCAL*evaluate(x,original)/depth,HORIZON+DEPTH_SCALE/depth)
                                        actual=projected_corner_expressions(row,end,offset)
                                        for expression,want in zip(actual,expected):
                                            self.assertAlmostEqual(evaluate(expression,values),want,places=9)

    def test_samples_are_shared_and_telemetry_ids_remain_stable(self):
        doc=Scene().build()
        road=doc.find("Artboard[@name='Road motion']")
        nodes=[n for n in road.findall('Node') if n.get('name','').startswith('Shared road sample')]
        self.assertEqual(len(nodes),32)
        self.assertEqual(len(SAMPLE_DEFAULTS),128)
        for name,value in SAMPLE_DEFAULTS.items():
            self.assertEqual(PROPERTIES[name],('Number',value))
            self.assertTrue(IDS[name].startswith('9:'))
        self.assertEqual(len(set(IDS.values())),len(IDS))
        self.assertNotIn('1:100',IDS.values())
        for node in nodes:
            publications=[b for b in node.findall('DataBindContext') if b.get('direction')=='true']
            self.assertEqual(len(publications),4)
        projection=[f for f in doc.findall('DataConverterFormula')
                    if f.get('name','').startswith(('Projected boundary','_laneSample'))]
        self.assertLess(sum(len(list(f.iter())) for f in projection),25000)


if __name__=='__main__':
    unittest.main()
