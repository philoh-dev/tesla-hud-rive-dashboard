"""Reviewed low-angle road and stable adjacent-vehicle projection for MYJ SG."""
from pathlib import Path
import math
import xml.etree.ElementTree as ET
from generate import ROAD_BEND_PIXELS, PARK, FORMULAS
ROOT = Path(__file__).resolve().parent

# Metres on a flat road. Calibrate the 2D road canvas against the baked sprite
# rather than claiming the sprite has a known 3D lens/camera calibration.
HORIZON = 145.0
FOCAL = 600.0
LANE_WIDTH = 3.4
PAINT_WIDTH = .12
PAINT_LENGTH = 6.0
CYCLE_LENGTH = 12.0
NEAR_Z = 6.0
FAR_Z = 186.0
EGO_CHASE_SCALE = 109/946
EGO_LOWERING = .20*875*EGO_CHASE_SCALE
ROAD_CONTACT_Y = 234 + 50/2.25 + 51
CONTACT_Y = ROAD_CONTACT_Y + EGO_LOWERING
CONTACT_Z = FOCAL/(109/2.0)
DEPTH_SCALE = (ROAD_CONTACT_Y-HORIZON)*CONTACT_Z
ADJACENT_CONTACT_Y = 374.0
ADJACENT_WORLD_WIDTH = 2.1
ADJACENT_LATERAL_OFFSET = 3.2
ADJACENT_Z = DEPTH_SCALE/(ADJACENT_CONTACT_Y-HORIZON)
EGO_CHASE_Y = CONTACT_Y-(1003-599.5)*EGO_CHASE_SCALE
CURVE_HEADING = math.radians(5)
CURVE_ACCELERATION = .0024
HORIZON_SHIFT_FRACTION = .20
# Set the arc's asymptotic heading so the VP reaches 20% of native canvas width.
# This changes the ground path itself; it is not an extra screen-space warp.
CURVE_TRANSITION = (800*HORIZON_SHIFT_FRACTION/FOCAL-CURVE_HEADING)/(.5*CURVE_ACCELERATION)
MAX_VEHICLE_HEADING = math.radians(6)

def ground_curve(z, bend):
    """Smooth ground arc with a signed finite horizon; no far-tangent switch."""
    d=z-CONTACT_Z
    return bend*(CURVE_HEADING*d+.5*CURVE_ACCELERATION*d*d/
                 (1+max(0,d)/CURVE_TRANSITION))

def vanishing_point_x(bend):
    return 400+FOCAL*bend*(CURVE_HEADING+.5*CURVE_ACCELERATION*CURVE_TRANSITION)

def ground_slope_expression(z, bend):
    d=f'(({z})-{CONTACT_Z})'
    q=f'max(0,{d})'
    return (f'({bend})*({CURVE_HEADING}+{CURVE_ACCELERATION}*'
            f'({d})*(1+({q})/{2*CURVE_TRANSITION})/'
            f'pow(1+({q})/{CURVE_TRANSITION},2))')

def ground_curve_expression(z, bend='_roadBend'):
    d=f'(({z})-{CONTACT_Z})'
    return (f'({bend})*({CURVE_HEADING}*{d}+'
            f'{.5*CURVE_ACCELERATION}*pow({d},2)/'
            f'(1+max(0,{d})/{CURVE_TRANSITION}))')

def lane_frame_expressions(z, offset, bend='_roadBend'):
    """Offset the ground centerline along its unit normal, before projection."""
    slope=ground_slope_expression(z,bend)
    normal=f'sqrt(1+pow(({slope}),2))'
    x=f'({ground_curve_expression(z,bend)})+{offset}/({normal})'
    depth=f'(({z})-({offset})*({slope})/({normal}))'
    return x,depth

def lane_heading_expression(z, offset, bend='input'):
    tangent=ground_slope_expression(str(z),bend)
    # Small-angle tangent of the offset lane; inside/outside lane radii differ.
    d=max(0,z-CONTACT_Z)
    acceleration=CURVE_ACCELERATION/pow(1+d/CURVE_TRANSITION,3)
    return f'min({MAX_VEHICLE_HEADING},max({-MAX_VEHICLE_HEADING},({tangent})/(1-({offset})*{acceleration}*{bend})))'

def heading_pose(scene, image, width, height, scale, heading, mirror=1, pivot=(0,0)):
    """Subtle image-plane heading cue for the existing 2D sprite.

    This is not a new 3D view: true yaw needs angle-specific artwork.
    """
    base_scale=float(image.get('scaleX','1'))
    angle=f'({mirror})*({heading})'
    scene.bind(image,'_roadBend',15,scene.formula(
        image.get('name')+' curve heading',angle))
    scene.bind(image,'_roadBend',16,scene.formula(
        image.get('name')+' heading foreshortening',
        f'{base_scale}*(1-.5*pow(({angle}),2))'))
    # Compensate rotation about the image center so its ground contact pivot
    # remains stationary. The same transform is used for the attached shadow.
    px,py=pivot
    for key,base,expression in (
        (13,float(image.get('x','0')),f'{px}*.5*pow(({angle}),2)+{py}*({angle})'),
        (14,float(image.get('y','0')),f'{py}*.5*pow(({angle}),2)-{px}*({angle})')):
        scene.bind(image,'_roadBend',key,scene.formula(
            image.get('name')+f' ground pivot compensation {key}',f'{base}+({expression})'))


def project(x, z):
    return 400+FOCAL*x/z, HORIZON+DEPTH_SCALE/z

def radial_contact(scene,parent,x,y,w,h,color,light=None):
    shape=scene.el(parent,'Shape',name='Soft radial ground contact',x=x,y=y,
                   scaleY=h/w,id=scene.ident())
    scene.el(shape,'Ellipse',width=w,height=w)
    radial=scene.el(scene.el(shape,'Fill'),'RadialGradient',
                   startX=0,startY=0,endX=w/2,endY=0)
    for position,factor in ((0,1),(.45,.65),(1,0)):
        alpha=round(int(color[:2],16)*factor)
        stop=scene.el(radial,'GradientStop',position=position,
                      colorValue=f'{alpha:02X}'+color[2:])
        if light:
            scene.theme_color(stop,color,light)

def stabilize_blind_spots(document):
    """Occupancy is presence, not a measured relative position or velocity."""
    main=document.find("Artboard[@name='Newhaven']")
    machine=main.find('StateMachine')
    for side in ('left','right'):
        layer=machine.find(f"StateMachineLayer[@name='{side} independent car motion']")
        assert layer is not None
        machine.remove(layer)
        for state in ('still','moving'):
            animation=main.find(f"LinearAnimation[@name='{side} car motion {state}']")
            assert animation is not None
            main.remove(animation)
        arrival=main.find(f".//Node[@name='{side} blind spot arrival']")
        arrival.set('x','0')
        arrival.set('y','0')
        for state in ('hidden','visible','exiting'):
            animation=main.find(f"LinearAnimation[@name='{side} arrival {state}']")
            animation.set('duration','1' if state=='hidden' else '8')
            for child in list(animation):
                animation.remove(child)
            obj=ET.SubElement(animation,'KeyedObject',objectId=arrival.get('id'))
            prop=ET.SubElement(obj,'KeyedProperty',propertyKey='18')
            frames={'hidden':((0,0),),'visible':((0,0),(8,1)),
                    'exiting':((0,1),(8,0))}[state]
            for frame,value in frames:
                ET.SubElement(prop,'KeyFrameDouble',frame=str(frame),value=str(value),
                              interpolationType='linear')
        # Opacity already supplies the entire transition, without another blend.
        layer=machine.find(f"StateMachineLayer[@name='{side} blind spot arrival']")
        for transition in layer.iter('StateTransition'):
            transition.set('duration','0')

def apply_projection(scene, document):
    stabilize_blind_spots(document)
    road=document.find("Artboard[@name='Road motion']")
    for node in list(road.findall('Node')):
        if 'lanes' in node.get('name','').lower():
            road.remove(node)
    from road_projection_cache import (ROWS,add_projection_cache,
                                       projected_corner_expressions,sample_name)
    add_projection_cache(scene,road)

    # First siblings draw on top: warnings, assist blue, then neutral theme.
    styles=(('left warning','FFE02020',-1),('right warning','FFE02020',1),
            ('Assist','FF0071FF',0),('Neutral','FFD9E0E3',0),
            ('Outer corridor','FF566068',0))
    for label,color,warning_side in styles:
        group=scene.node(road,label+' lanes')
        if warning_side:
            side_name='left' if warning_side<0 else 'right'
            scene.opacity(group,side_name+'BlindSpot',
                          f'min(1,max(0,input))*min(1,max(0,{side_name}Blinker))',
                          'Projected '+side_name+' warning visibility')
        elif label=='Assist':
            scene.bind(group,'adasOn',18,'2:3')
        for side in ((warning_side,) if warning_side else (-1,1)):
            boundary=3 if label=='Outer corridor' else 1
            lane_parent=group
            if label=='Outer corridor':
                side_name='left' if side<0 else 'right'
                lane_parent=scene.node(group,side_name+' occupied outer boundary')
                scene.opacity(lane_parent,side_name+'BlindSpot',
                              FORMULAS[side_name+' Occupied'],
                              side_name+' outer boundary occupancy')
            for row in range(ROWS):
                # Translate painted ground strips in metres, then project every
                # corner. Clamp only at clip planes; no linear screen-space lerp.
                base=NEAR_Z+row*CYCLE_LENGTH
                corners=((-.5,0),(-.5,1),(.5,1),(.5,0))
                initial=[]
                expressions=[]
                for lateral,endpoint in corners:
                    x_world=side*LANE_WIDTH/2*boundary+lateral*PAINT_WIDTH
                    z0=min(FAR_Z,max(NEAR_Z,base+endpoint*PAINT_LENGTH))
                    initial.append(project(x_world,z0))
                    expressions.append(projected_corner_expressions(row,endpoint,x_world))
                light='FFB9C1C7' if label=='Outer corridor' else 'FFECF0F1' if label=='Neutral' else None
                vertices=scene.polygon(lane_parent,f'Projected {label} {side} dash {row}',
                                       initial,color,light=light)
                for i,(vertex,(x,y)) in enumerate(zip(vertices,expressions)):
                    vertex.set('radius','0')
                    for key,expression in ((24,x),(25,y)):
                        scene.bind(vertex,sample_name(row,corners[i][1],'Depth'),key,scene.formula(
                            f'Projected boundary {boundary} {side} {row} corner {i} coordinate {key}',expression))

    native=document.find(".//Node[@name='Native 800 pixel scene']")
    # Replace the legacy screen-space steering translation, including the nested
    # road offset, so every surface uses one projected ground path exactly once.
    for name,tag in (('left blind spot','Node'),('right blind spot','Node'),
                     ('Speed driven road','NestedArtboard')):
        target=native.find(f"{tag}[@name='{name}']")
        for binding in list(target.findall("DataBindContext[@propertyKey='13']")):
            target.remove(binding)
    # One world-space lane center and depth control each car's X, tire Y and
    # size. Anchor to the actual opaque tire baseline, not the PNG canvas edge.
    # Measurements baked from the approved RGBA sprite (alpha >= 128).
    # Keep builds stdlib-only; asset checksums lock these silhouette metrics.
    body_width = 199
    density = 2.0
    foot = 67.0
    scale=(FOCAL*ADJACENT_WORLD_WIDTH/ADJACENT_Z)/body_width
    wheel_contacts = [(-80.41935483870968, 61.0), (47.44736842105263, 67.0), (85.83333333333334, 25.0)]
    rear_x=sum(x for x,y in wheel_contacts[:2])/2
    rear_y=sum(y for x,y in wheel_contacts[:2])/2
    for side,sign in (('left',-1),('right',1)):
        target,contact_y=project(sign*ADJACENT_LATERAL_OFFSET,ADJACENT_Z)
        mirror=-sign
        car=native.find(f"Node[@name='{side} blind spot']")
        local=car.find(f".//Node[@name='{side} independent car motion']")
        images=list(local.findall('Image'))
        placement=scene.node(local,side+' projected lane placement',
                             target-float(car.get('x'))-mirror*rear_x*scale,
                             contact_y-foot*scale-float(car.get('y')),
                             scaleX=mirror*scale,scaleY=scale)
        world_x,world_z=lane_frame_expressions(str(ADJACENT_Z),sign*ADJACENT_LATERAL_OFFSET,'input')
        ratio=f'({ADJACENT_Z}/({world_z}))'
        scene.bind(placement,'_roadBend',13,scene.formula(side+' curved lane anchor',
                   f'400+{FOCAL}*({world_x})/({world_z})-{float(car.get("x"))}-{mirror*rear_x*scale}*{ratio}'))
        scene.bind(placement,'_roadBend',14,scene.formula(side+' curved lane contact depth',
                   f'{HORIZON}+{DEPTH_SCALE}/({world_z})-{foot*scale}*{ratio}-{float(car.get("y"))}'))
        for key,factor in ((16,mirror*scale),(17,scale)):
            scene.bind(placement,'_roadBend',key,scene.formula(side+f' curved lane scale {key}',f'{factor}*{ratio}'))
        heading=lane_heading_expression(ADJACENT_Z,sign*ADJACENT_LATERAL_OFFSET)
        for image in images:
            local.remove(image)
            # Left is viewed from rear-right; right shows its mirrored inner
            # left flank. No roll/flat-image rotation that implies lane crossing.
            image.set('scaleX','1')
            image.set('rotation','0')
            heading_pose(scene,image,234,280,scale,heading,mirror,pivot=(rear_x,foot))
            placement.append(image)
        shadow=scene.node(placement,side+' attached tire and chassis occlusion')
        heading_pose(scene,shadow,234,280,scale,heading,mirror,pivot=(rear_x,foot))
        patches=[(x,y+.2*density,9*density,3.5*density,'D0000000',None) for x,y in wheel_contacts]
        patches.extend(((rear_x,rear_y,body_width*.88,6*density,'90000000',None),
                        (rear_x,rear_y+.5*density,body_width*1.08,10*density,'90343A40','90000000')))
        for x,y,w,h,color,light in patches:
            radial_contact(scene,shadow,x,y,w,h,color,light)
        assert contact_y>CONTACT_Y
        assert FOCAL*ADJACENT_WORLD_WIDTH/ADJACENT_Z>109
    ego=native.find("Image[@name='Driving ego vehicle']")
    ego.set('x','400')
    ego.set('y',str(EGO_CHASE_Y))
    ego.set('scaleX',str(EGO_CHASE_SCALE))
    ego.set('scaleY',str(EGO_CHASE_SCALE))
    ego_heading=lane_heading_expression(CONTACT_Z,0)
    heading_pose(scene,ego,1312,1199,EGO_CHASE_SCALE,ego_heading,pivot=(0,CONTACT_Y-EGO_CHASE_Y))
    ground=scene.node(native,'Driving tire and chassis contact',400,EGO_CHASE_Y)
    heading_pose(scene,ground,109,124,1,ego_heading,pivot=(0,CONTACT_Y-EGO_CHASE_Y))
    scene.opacity(ground,'gear',f'1-({PARK})','Driving contact shadow visible')
    native.remove(ground)
    native.insert(list(native).index(ego)+1,ground)
    # Theme the ambient receiving patch; contact occlusion is black in both
    # themes. The parent follows the ego vehicle's Park/Drive visibility.
    for x,y,w,h,color,light in ((356,CONTACT_Y-.5,12,5,'D0000000',None),
                                (444,CONTACT_Y-.5,12,5,'D0000000',None),
                                (400,CONTACT_Y,96,10,'98000000',None),
                                (400,CONTACT_Y+2,118,18,'90343A40','90000000')):
        radial_contact(scene,ground,x-400,y-EGO_CHASE_Y,w,h,color,light)
