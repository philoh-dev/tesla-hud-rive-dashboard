"""Shared Park-only ground shading for individual and universal dashboards."""
from copy import deepcopy


def park_wheel_contacts(vehicle):
    """Tyre contact points in native scene space, measured on the parked art.

    Park sprites share a 410px width but not wheel positions. In particular,
    the Highland's tyres end above the bottom of its transparent image.
    """
    if vehicle.startswith('model-3-highland-'):
        return ((368,366),(563,283))
    if vehicle.startswith('model-y-legacy-'):
        return ((369,375),(559,292))
    if vehicle.startswith('model-y-juniper-'):
        return ((369,383),(559,300))
    return ((371,382),(558,306))


def park_ground_outline(vehicle):
    """A single ground-plane footprint, not a flattened image silhouette.

    The front edge follows the bumper; the long near edge joins the two
    tyre contact points across the clearance below the rocker panel.
    """
    front,rear=park_wheel_contacts(vehicle)
    if vehicle.startswith('model-3-highland-'):
        nose=((211,329),(230,339),(260,352),(300,361),(340,361))
    elif vehicle.startswith('model-y-legacy-'):
        nose=((200,317),(220,333),(240,344),(280,360),(320,367),(345,368))
    elif vehicle.startswith('model-y-juniper-'):
        nose=((200,332),(220,346),(240,356),(280,372),(320,378),(345,379))
    else:
        nose=((200,342),(220,354),(240,363),(280,375),(320,381),(345,381))
    points=[*nose,(front[0],front[1]+2),(front[0]+22,front[1]-5),
            (rear[0]-18,rear[1]+9),(rear[0]+4,rear[1]+2),
            (rear[0]+24,rear[1]-10),(rear[0]+36,rear[1]-30),
            (rear[0]-30,rear[1]-58),(front[0]-120,front[1]-70)]
    # Positive signed area is clockwise in the screen's downward Y axis.
    area=sum(x*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*y
             for i,(x,y) in enumerate(points))
    return points if area>0 else list(reversed(points))


def add_park_ground(scene,document,vehicles=None):
    """Ground the parked sprite without changing its artwork or Drive scene."""
    parent=document.find(".//Node[@name='Native 800 pixel scene']")
    park=next(n for n in parent if n.get('name') in
              ('Vehicle park selector','Park front three-quarter vehicle'))
    ground=parent.find("Node[@name='Park ground']")
    if ground is None:
        ground=scene.node(parent,'Park ground')
        # Share the parked vehicle's exact gear gate, without a second formula.
        for binding in park.findall('DataBindContext'):
            ground.append(deepcopy(binding))
        # First siblings paint on top in Rive.
        parent.remove(ground)
        parent.insert(list(parent).index(park)+1,ground)
        solo=scene.el(ground,'Solo',id=scene.ident(),name='Vehicle ground selector')
    else:
        solo=ground.find('Solo')

    designs=vehicles or (scene.assets['park'].split('/')[-2],)
    children={}
    for vehicle in designs:
        existing=solo.find(f"Node[@name='{vehicle} ground']")
        if existing is not None:
            children[vehicle]=existing.get('id')
            continue
        design=scene.node(solo,vehicle+' ground')
        children[vehicle]=design.get('id')
        front,_=park_wheel_contacts(vehicle)
        for theme,expression,ambient,body in (
                ('Dark','darkMode','FF60666B','B0000000'),
                ('Light','1-darkMode','38000000','98000000')):
            layer=scene.node(design,theme+' park ground')
            scene.opacity(layer,'darkMode',expression,theme+' park ground visible')
            shape=scene.el(layer,'Shape',name='Continuous projected footprint',id=scene.ident())
            path=scene.el(shape,'PointsPath',name='Ground plane outline',isClosed=True,isClockwise=True)
            for x,y in park_ground_outline(vehicle):
                scene.el(path,'StraightVertex',x=x,y=y,radius=9)
            # Both paints share ONE geometry: a soft penumbra and a denser
            # near-edge shadow. There are no detached tyre pads or ellipses.
            fill=scene.el(shape,'Fill',name='Soft penumbra',fillRule='clockwise')
            scene.el(fill,'SolidColor',colorValue=ambient)
            scene.el(fill,'Feather',name='Soft outer edge',strength=12,spaceValue='local')
            fill=scene.el(shape,'Fill',name='Continuous contact shading',fillRule='clockwise')
            gradient=scene.el(fill,'LinearGradient',name='Ground depth falloff',
                              startX=front[0],startY=front[1],
                              endX=front[0]-38,endY=front[1]-90)
            for position,alpha in ((0,1),(0.4,0.75),(1,0.15)):
                value=round(int(body[:2],16)*alpha)
                scene.el(gradient,'GradientStop',position=position,colorValue=f'{value:02X}'+body[2:])
            scene.el(fill,'Feather',name='Contact edge softness',strength=4,spaceValue='local')
    solo.set('activeComponentId',children.get('generic-vehicle',next(iter(children.values()))))
    return solo,children
