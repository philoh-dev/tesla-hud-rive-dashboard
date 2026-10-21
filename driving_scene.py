"""Driving scene enhancements shared by every vehicle and universal dashboard."""
from copy import deepcopy


def enhance_driving(scene, document, properties):
    # Warning dashes mirror the road geometry, phase, steering, and theme.
    road=document.find("Artboard[@name='Road motion']")
    neutral=road.find("Node[@name='Neutral lanes']")
    assist=road.find("Node[@name='Assist lanes']")
    for side,sign in (('left',-1),('right',1)):
        warning=scene.node(road,side+' blind spot warning lanes')
        scene.opacity(warning,side+'BlindSpot',
                      f'min(1,max(0,input))*min(1,max(0,{side}Blinker))',
                      side+' occupied and indicating')
        for shape in neutral.findall('Shape'):
            if not shape.get('name','').startswith(f'Lane Neutral lanes {sign} '):
                continue
            duplicate=deepcopy(shape)
            duplicate.set('name',shape.get('name').replace('Neutral lanes','Warning lanes'))
            for element in duplicate.iter():
                if 'id' in element.attrib:
                    element.set('id',scene.ident())
            ink=duplicate.find('Stroke/SolidColor')
            for child in list(ink):
                ink.remove(child)
            ink.set('colorValue','FFE02020')
            warning.append(duplicate)
        assert len(warning.findall('Shape'))==7
        road.remove(warning)
        road.insert(list(road).index(assist),warning)

    main=document.find("Artboard[@name='Newhaven']")
    main.find(".//LayoutComponent[@name='Driving region 80 percent']").set('clip','true')
    machine=main.find('StateMachine')
    native=main.find(".//Node[@name='Native 800 pixel scene']")
    for tag,name in (('Image','Driving ego vehicle'),('Node','left blind spot'),
                     ('Node','right blind spot'),('Node','Forward stopped direction'),
                     ('Node','Reverse stopped direction')):
        element=native.find(f"{tag}[@name='{name}']")
        element.set('y',str(float(element.get('y'))+16))
    PROPERTIES=properties
    motions={}
    # A brisk 500 ms motion: decelerate into the lane, accelerate out of it.
    MOTION_FRAMES=30
    FADE_FRAMES=5
    
    def condition(transition,prop,value,operator='equal'):
        kind=PROPERTIES[prop][0]
        node=scene.el(transition,'TransitionViewModelCondition',opValue=operator)
        comparator=scene.el(node,'TransitionPropertyViewModelComparator')
        scene.bind(scene.el(comparator,'BindableProperty'+kind),prop,634 if kind=='Boolean' else 636)
        scene.el(node,'TransitionValue'+kind+'Comparator',value=value)
    
    for side in ('left','right'):
        group=native.find(f"Node[@name='{side} blind spot']")
        # The state machine owns visibility so a cleared flag cannot cut off exit.
        for binding in list(group.findall('DataBindContext')):
            if binding.get('propertyKey')=='18':
                group.remove(binding)
        # Adjacent-lane centers diverge with depth at twice the lane-border slope.
        # Match this design's road perspective rather than rising vertically.
        entry_x=(-1 if side=='left' else 1)*2*scene.road_spread/384*160
        motion=scene.node(group,side+' blind spot arrival',entry_x,160,opacity=0)
        motions[side]=motion
        for image in list(group.findall('Image')):
            group.remove(image)
            motion.append(image)
        layer=scene.el(machine,'StateMachineLayer',name=side+' blind spot arrival',id=scene.ident())
        scene.el(layer,'AnyState',x=0,y=-120)
        scene.el(layer,'ExitState',x=600,y=-120)
        entry=scene.el(layer,'EntryState',x=0,y=0)
        states={name:scene.ident() for name in ('hidden','visible','exiting')}
        animations={name:scene.ident() for name in states}
        scene.el(entry,'StateTransition',stateToId=states['hidden'])
        nodes={name:scene.el(layer,'AnimationState',id=states[name],animationId=animations[name],
                             reset=True,x=200+200*index,y=0) for index,name in enumerate(states)}
        for source in ('hidden','exiting'):
            for prop,value in (('alwaysOnBlindSpotMonitor',True),(side+'Blinker',0)):
                t=scene.el(nodes[source],'StateTransition',stateToId=states['visible'],
                           duration=80 if source=='exiting' else 0)
                condition(t,side+'BlindSpot',0,'greaterThan')
                condition(t,'gear',2,'greaterThanOrEqual')
                condition(t,'gear',4,'lessThanOrEqual')
                condition(t,prop,value,'equal' if prop=='alwaysOnBlindSpotMonitor' else 'greaterThan')
        for source in ('visible','exiting'):
            for value,op in ((2,'lessThan'),(4,'greaterThan')):
                condition(scene.el(nodes[source],'StateTransition',stateToId=states['hidden'],duration=0),
                          'gear',value,op)
        condition(scene.el(nodes['visible'],'StateTransition',stateToId=states['exiting'],duration=80),
                  side+'BlindSpot',0,'lessThanOrEqual')
        t=scene.el(nodes['visible'],'StateTransition',stateToId=states['exiting'],duration=80)
        condition(t,'alwaysOnBlindSpotMonitor',False)
        condition(t,side+'Blinker',0,'lessThanOrEqual')
        scene.el(nodes['exiting'],'StateTransition',stateToId=states['hidden'],duration=0,
                 enableExitTime=True,exitTimeIsPercetange=True,exitTime=100)
        for name in states:
            animation=scene.el(main,'LinearAnimation',name=side+' arrival '+name,id=animations[name],
                                duration=1 if name=='hidden' else MOTION_FRAMES,fps=60,loopValue='oneShot')
            values={
                'visible':((13,((0,entry_x),(MOTION_FRAMES,0))),(14,((0,160),(MOTION_FRAMES,0))),(18,((0,0),(FADE_FRAMES,1)))),
                'exiting':((13,((0,0),(MOTION_FRAMES,entry_x))),(14,((0,0),(MOTION_FRAMES,160))),(18,((0,1),(MOTION_FRAMES-FADE_FRAMES,1),(MOTION_FRAMES,0)))),
                'hidden':((13,((0,entry_x),)),(14,((0,160),)),(18,((0,0),))),
            }[name]
            for key,frames in values:
                prop=scene.el(scene.el(animation,'KeyedObject',objectId=motion.get('id')),
                              'KeyedProperty',propertyKey=key)
                for index,(frame,value) in enumerate(frames):
                    node=scene.el(prop,'KeyFrameDouble',frame=frame,value=value,
                                  interpolationType='cubic' if index<len(frames)-1 else 'linear')
                    if index<len(frames)-1:
                        curve=dict(x1=.42,y1=0,x2=1,y2=1) if name=='exiting' else dict(x1=0,y1=0,x2=.58,y2=1)
                        scene.el(node,'CubicEaseInterpolator',**curve)
    
    # The existing smoothed steering signal curves the distant road. Translate its
    # near edges in the opposite direction to show the fixed ego car changing its
    # position within the lane; neighboring vehicles follow that road translation.
    for name,scale in (('left blind spot',-8),('right blind spot',-8),
                       ('Speed driven road',-8)):
        tag='NestedArtboard' if name=='Speed driven road' else 'Node'
        target=native.find(f"{tag}[@name='{name}']")
        assert target is not None
        base=float(target.get('x','0'))
        scene.bind(target,'_roadBend',13,scene.formula(name+' steering shift',
                                                       f'{base}+{scale}*input'))
    
    # Local movement is nested inside the arrival motion and steering-shifted car
    # group. Its X/Y values therefore add to the road's steering offset on screen.
    # Each neighboring car has independent, intermittent corrections.
    car_schedules={
        'left': ((5,2.0,8,-5),(12,2.8,-7,10),(18,2.2,10,-9),(7,2.5,0,0)),
        'right': ((9,2.4,-10,7),(6,2.7,8,-8),(20,2.0,-5,10),(11,2.6,0,0)),
    }
    for side,schedule in car_schedules.items():
        arrival=motions[side]
        images=list(arrival.findall('Image'))
        assert len(images)==2
        local=scene.node(arrival,side+' independent car motion',0,0)
        for image in images:
            arrival.remove(image)
            local.append(image)
        t=0
        x=y=0
        x_path=[(0,0)]
        y_path=[(0,0)]
        for hold,travel,next_x,next_y in schedule:
            assert 5<=hold<=20 and abs(next_x)<=10 and abs(next_y)<=10
            t+=hold
            x_path.append((round(t*60),x))
            y_path.append((round(t*60),y))
            t+=travel
            x,y=next_x,next_y
            x_path.append((round(t*60),x))
            y_path.append((round(t*60),y))
        assert (x,y)==(0,0)
        layer=scene.el(machine,'StateMachineLayer',name=side+' independent car motion',id=scene.ident())
        entry=scene.el(layer,'EntryState',x=0,y=0)
        scene.el(layer,'AnyState',x=0,y=-120)
        scene.el(layer,'ExitState',x=600,y=-120)
        states={name:scene.ident() for name in ('still','moving')}
        animations={name:scene.ident() for name in states}
        scene.el(entry,'StateTransition',stateToId=states['still'])
        nodes={name:scene.el(layer,'AnimationState',id=states[name],animationId=animations[name],
                            reset=True,x=200+200*i,y=0) for i,name in enumerate(states)}
        start=scene.el(nodes['still'],'StateTransition',stateToId=states['moving'],duration=400)
        condition(start,'egoSpeed',0,'greaterThan')
        condition(start,'gear',2,'greaterThanOrEqual')
        condition(start,'gear',4,'lessThanOrEqual')
        for prop,value,op in (('egoSpeed',0,'lessThanOrEqual'),('gear',2,'lessThan'),('gear',4,'greaterThan')):
            condition(scene.el(nodes['moving'],'StateTransition',stateToId=states['still'],duration=400),prop,value,op)
        for name in states:
            animation=scene.el(main,'LinearAnimation',name=side+' car motion '+name,id=animations[name],
                               duration=round(t*60) if name=='moving' else 1,fps=60,
                               loopValue='loop' if name=='moving' else 'oneShot')
            obj=scene.el(animation,'KeyedObject',objectId=local.get('id'))
            for key,path in ((13,x_path),(14,y_path)):
                prop=scene.el(obj,'KeyedProperty',propertyKey=key)
                for frame,pixels in (path if name=='moving' else ((0,0),)):
                    node=scene.el(prop,'KeyFrameDouble',frame=frame,value=pixels/2.25,
                                  interpolationType='cubic')
                    scene.el(node,'CubicEaseInterpolator',x1=.42,y1=0,x2=.58,y2=1)
