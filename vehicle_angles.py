"""Exclusive view-specific MYJ SG sprites, without crossfade ghosting or roll."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parent
ASSET_DIR='assets/vehicle/model-y-juniper-stealth-grey/view-angles'
POSE_ASSETS={
    'ego': ASSET_DIR+'/ego-back-left-middle.png',
    'grey_narrow': ASSET_DIR+'/grey-narrow.png',
    'grey_wide': ASSET_DIR+'/grey-wide.png',
    'red_narrow': ASSET_DIR+'/red-narrow.png',
    'red_wide': ASSET_DIR+'/red-wide.png',
}
POSE_THRESHOLD=50
# Opaque body height of drive-chase.png (alpha >=224): y129..1004.
EGO_BODY_HEIGHT=875

def select_pose(current,angle):
    """Reference model: angled views only outside +/-50 steering-wheel degrees."""
    if angle>POSE_THRESHOLD:
        return 1
    if angle<-POSE_THRESHOLD:
        return -1
    return 0

def pose_machine(scene,doc,solo,poses,label):
    main=doc.find("Artboard[@name='Newhaven']")
    machine=main.find('StateMachine')
    layer=scene.el(machine,'StateMachineLayer',name=label+' exclusive pose',id=scene.ident())
    entry=scene.el(layer,'EntryState')
    scene.el(layer,'AnyState')
    scene.el(layer,'ExitState')
    states={pose:scene.ident() for pose in (0,1,-1)}
    scene.el(entry,'StateTransition',stateToId=states[0],duration=0)
    nodes={}
    for pose in states:
        animation_id=scene.ident()
        nodes[pose]=scene.el(layer,'AnimationState',id=states[pose],animationId=animation_id,reset=True)
        animation=scene.el(main,'LinearAnimation',name=label+f' exclusive pose {pose}',
                           id=animation_id,duration=1,fps=60,loopValue='oneShot')
        prop=scene.el(scene.el(animation,'KeyedObject',objectId=solo.get('id')),
                      'KeyedProperty',propertyKey=296)
        scene.el(prop,'KeyFrameId',frame=0,value=poses[pose],interpolationType='hold')
    rules={0:((1,(('greaterThan',POSE_THRESHOLD),)),
              (-1,(('lessThan',-POSE_THRESHOLD),))),
           1:((-1,(('lessThan',-POSE_THRESHOLD),)),
              (0,(('lessThanOrEqual',POSE_THRESHOLD),('greaterThanOrEqual',-POSE_THRESHOLD)))),
          -1:((1,(('greaterThan',POSE_THRESHOLD),)),
              (0,(('greaterThanOrEqual',-POSE_THRESHOLD),('lessThanOrEqual',POSE_THRESHOLD))))}
    for source,transitions in rules.items():
        for target,conditions in transitions:
            transition=scene.el(nodes[source],'StateTransition',stateToId=states[target],duration=0)
            for operator,value in conditions:
                condition=scene.el(transition,'TransitionViewModelCondition',opValue=operator)
                comparator=scene.el(condition,'TransitionPropertyViewModelComparator')
                scene.bind(scene.el(comparator,'BindablePropertyNumber'),'egoSteeringAngle',636)
                scene.el(condition,'TransitionValueNumberComparator',value=value)

def apply_angle_sprites(scene,doc):
    poses=POSE_ASSETS
    geometry=json.loads((ROOT/ASSET_DIR/'geometry.json').read_text(encoding='utf-8'))
    native=doc.find(".//Node[@name='Native 800 pixel scene']")
    asset_ids={}
    for i,(key,path) in enumerate(poses.items()):
        identity=f'5:{700+i}'
        asset_ids[key]=identity
        scene.el(doc,'ImageAsset',id=identity,name='Angle '+key,file=path)
    parents={c:p for p in doc.iter() for c in p}
    images=[im for im in native.iter('Image') if im.get('name')=='Driving ego vehicle' or im.get('name') in (f'{side} {color} vehicle' for side in ('left','right') for color in ('red','grey'))]
    for original in images:
        name=original.get('name')
        is_ego=name=='Driving ego vehicle'
        parent=parents[original]
        index=list(parent).index(original)
        for binding in list(original.findall('DataBindContext')):
            if binding.get('propertyKey') in ('13','14','15','16','17'):
                original.remove(binding)
        group=scene.node(parent,name+' view selector',float(original.get('x','0')),float(original.get('y','0')),
                         scaleX=float(original.get('scaleX','1')),scaleY=float(original.get('scaleY','1')))
        parent.remove(group)
        parent.remove(original)
        parent.insert(index,group)
        for binding in list(original.findall("DataBindContext[@propertyKey='18']")):
            original.remove(binding)
            group.append(binding)
        for key,value in dict(x=0,y=0,scaleX=1,scaleY=1,rotation=0).items():
            original.set(key,str(value))
        solo=scene.el(group,'Solo',name=name+' exclusive poses',id=scene.ident(),
                      activeComponentId=original.get('id'))
        pose_ids={0:original.get('id')}
        if is_ego:
            specifications=((1,'ego',-1),(-1,'ego',1))
            body_width,foot,rear_x=946,403.5,0
        else:
            side,color,_=name.split()
            specifications=((1,color+('_wide' if side=='left' else '_narrow'),1),
                            (-1,color+('_narrow' if side=='left' else '_wide'),1))
            body_width,foot,rear_x=199,67,(-80.41935483870968+47.44736842105263)/2
        for direction,key,mirror in specifications:
            (w,h),box,center=geometry[key]
            # Match ego height rather than width: the angled silhouette is
            # naturally wider, but must not shrink when its pose is selected.
            scale=EGO_BODY_HEIGHT/(box[3]-box[1]) if is_ego else body_width/(box[2]-box[0])
            image=scene.el(solo,'Image',name=name+f' actual angle {direction}',id=scene.ident(),assetId=asset_ids[key],
                           x=rear_x-mirror*center*scale,y=foot-(box[3]-1-h/2)*scale,
                           scaleX=mirror*scale,scaleY=scale,rotation=0,samplerFilter='bilinear')
            pose_ids[direction]=image.get('id')
        solo.append(original)
        pose_machine(scene,doc,solo,pose_ids,name)
    # Ground shadows keep their flat-road orientation; anchors still follow the arc.
    for node in native.iter('Node'):
        if node.get('name')=='Driving tire and chassis contact' or 'attached tire and chassis occlusion' in node.get('name',''):
            for binding in list(node.findall('DataBindContext')):
                if binding.get('propertyKey') in ('13','14','15','16','17'):
                    node.remove(binding)
            node.set('rotation','0')
