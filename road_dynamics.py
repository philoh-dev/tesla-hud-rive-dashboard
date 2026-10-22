"""Speed-scaled road texture vibration without changing vehicle artwork.

Native displacement is capped at 0.5 output pixels at the 1800x1080 design size.
The same distance phase drives all lanes and blind-spot body vibration.
"""
import math
from myj_projection import ADJACENT_Z,ADJACENT_LATERAL_OFFSET,lane_frame_expressions
from generate import equal

AMPLITUDE_PIXELS=.5
DESIGN_SCALE=2.25
BODY_CYCLES=4

def dynamics_expressions(base_y):
    allowed=f'min(1,({equal("gear",2)})+({equal("gear",4)}))'
    amplitude=f'(min(1,max(0,egoSpeed)*(1+0.609344*input)/100)*({allowed}))'
    body=f'{2*math.pi*BODY_CYCLES}*_roadPhase'
    return {
        'body_y':f'{base_y}+{AMPLITUDE_PIXELS/DESIGN_SCALE}*{amplitude}*sin({body})',
    }

def bind_units(scene,target,key,expression,name):
    # Independent Boolean->numeric conversion matches the validated road clock.
    text_id,number_id=scene.ident(),scene.ident()
    scene.el(scene.document,'DataConverterToString',id=text_id,name=name+' units text')
    scene.el(scene.document,'DataConverterToNumber',id=number_id,name=name+' units number')
    formula=scene.formula(name,expression)
    scene.bind(target,'isImperial',key,scene.chain(name+' typed units',text_id,number_id,formula))

def add_dynamics(scene,doc):
    native=doc.find(".//Node[@name='Native 800 pixel scene']")
    for side in ('left','right'):
        placement=native.find(f".//Node[@name='{side} projected lane placement']")
        # Nest body-only motion under the projected anchor; contact shadows stay
        # grounded and all existing curvature/arrival bindings remain intact.
        vibration=scene.node(placement,side+' road vibration')
        placement.remove(vibration)
        placement.insert(0,vibration)
        for node in list(placement.findall('Node')):
            if node.get('name','').endswith(' vehicle view selector'):
                placement.remove(node)
                vibration.append(node)
        _,world_z=lane_frame_expressions(str(ADJACENT_Z),-ADJACENT_LATERAL_OFFSET if side=='left' else ADJACENT_LATERAL_OFFSET,'_roadBend')
        scale=float(placement.get('scaleY'))
        displacement=dynamics_expressions(0)['body_y']
        bind_units(scene,vibration,14,f'({displacement})*({world_z})/{ADJACENT_Z}/{scale}',side+' speed scaled road vibration')
