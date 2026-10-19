#!/usr/bin/env python3
"""Port the native Newhaven road_scene to script-free RML (Rive CLI 1.6.0).

Schema/property keys are from the official CLI, not private binary encoding.
Formula expressions below are also evaluated by the independent contract tests.
"""
import ast
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
DEFAULT_VEHICLE = 'model-y-juniper-stealth-grey'
VEHICLES = (DEFAULT_VEHICLE, 'model-3-highland-stealth-grey',
            'model-y-juniper-white-multi-coat', 'model-y-juniper-diamond-black',
            'model-y-juniper-marine-blue', 'model-y-juniper-quicksilver',
            'model-y-juniper-ultra-red')
VEHICLE_ASSET_DIR = f'assets/vehicle/{DEFAULT_VEHICLE}'
# Repository-relative assets; blind-spot cars and indicators are shared.
ASSETS = {
    "ego": f"{VEHICLE_ASSET_DIR}/drive.png",
    "park": f"{VEHICLE_ASSET_DIR}/park.png",
    "left_red": "assets/blind-spot-left-wide.png",
    "left_grey": "assets/blind-spot-left-grey-wide.png",
    "right_red": "assets/blind-spot-right-wide.png",
    "right_grey": "assets/blind-spot-right-grey-wide.png",
    "autopilot": "assets/autopilot-road-scene-wide.png",
}
IMAGE_IDS = {name: f"5:{index+1}" for index, name in enumerate(ASSETS)}


def vehicle_assets(vehicle=DEFAULT_VEHICLE):
    if vehicle not in VEHICLES:
        raise ValueError(f'Unsupported vehicle: {vehicle}')
    return dict(ASSETS, ego=f'assets/vehicle/{vehicle}/drive.png',
                park=f'assets/vehicle/{vehicle}/park.png')


PROPERTIES = {
    "egoSpeed": ("Number", 130), "gear": ("Number", 4),
    "leftBlinker": ("Number", 2), "rightBlinker": ("Number", 0),
    "leftBlindSpot": ("Number", 1), "rightBlindSpot": ("Number", 1),
    "fusedSpeedLimit": ("Number", 130), "adasOn": ("Boolean", True),
    "fullPackEnergy": ("Number", 79), "nominalEnergyRemaining": ("Number", 41.76),
    "energyBuffer": ("Number", 3), "powerLevel": ("Number", 25),
    "packVoltage": ("Number", 400), "packCurrent": ("Number", 200),
    "maxDischargePower": ("Number", 320), "maxRegenPower": ("Number", 80),
    "isImperial": ("Boolean", False), "showCarBattery": ("Boolean", True),
    "alwaysOnBlindSpotMonitor": ("Boolean", True),
    "dataSourceType": ("String", "demo"),
    "darkMode": ("Boolean", True),
    # Expose the host setting, but deliberately ignore it for the OLED black
    # background: dark mode must remain #000000 even when gray is requested.
    "darkModeBackgroundGray": ("Number", 0),
}
IDS = {key: f"1:{index + 10}" for index, key in enumerate(PROPERTIES)}


def equal(value, number):
    return f"max(0,1-sqrt(pow(({value})-{number},2)))"


def turn_signal_points(side):
    """Original geometric arrow, drawn without imported/traced bitmap artwork."""
    if side not in ('left','right'):
        raise ValueError(f'Unsupported turn-signal side: {side}')
    direction=1 if side=='left' else -1
    outline=((-16,0),(1,-15),(1,-5),(16,-5),(16,5),(1,5),(1,15))
    return [(direction*x,y) for x,y in outline]


def direction_arrow_points(direction):
    """Slim road-plane arrow projected from a 45-degree elevated viewpoint.

    Apply reverse before projection: the near end broadens and the far end
    narrows consistently with the road, rather than flipping a flat UI icon.
    """
    outline=((-11,-9),(-3,-9),(-3,22),(3,22),(3,-9),(11,-9),(0,-26))
    tilt=2**-.5
    # The lower reverse cue is nearer the viewer: give it a larger road-plane
    # footprint as well as the projection's natural near-field widening.
    size=1.20 if direction>0 else 1.50
    result=[]
    for x,y in outline:
        x*=size
        y*=direction*size
        perspective=180/(180-y*tilt)
        result.append((x*perspective,y*tilt*perspective))
    return result


PARK = equal("gear", 1)
DRIVE = f"min(1,{equal('gear', 2)}+{equal('gear', 3)}+{equal('gear', 4)})"
AVAILABLE = "max(0,round(fullPackEnergy*100)-round(energyBuffer*100))"
BATTERY = ("floor(min(100,max(0,(round(nominalEnergyRemaining*100)-"
           f"round(energyBuffer*100))*100/max(1,{AVAILABLE}))))")
BATTERY_VISIBLE = f"showCarBattery*min(1,max(0,nominalEnergyRemaining*100))*min(1,{AVAILABLE})"
PHYSICAL_SPEED = "max(0,egoSpeed)*(1+0.609344*isImperial)"
ROAD_RATE = f"({PHYSICAL_SPEED})/43.2*({equal('gear',4)}-{equal('gear',2)})"
FORMULAS = {
    "Park": PARK, "Driving": DRIVE, "Battery Percent": BATTERY,
    "Battery Visible": BATTERY_VISIBLE, "Road Rate": ROAD_RATE,
    "Power Up": "min(100,max(0,input))*1.44",
    "Power Down": "min(100,max(0,0-input))*1.44",
}
for side in ("left", "right"):
    blink, blind = f"{side}Blinker", f"{side}BlindSpot"
    FORMULAS[side + " Arrow"] = f"min(1,max(0,input))*(0.5+0.5*({equal('input',2)}))"
    FORMULAS[side + " Occupied"] = f"min(1,max(0,{blind}))*min(1,alwaysOnBlindSpotMonitor+min(1,{blink}))*({DRIVE})"
    FORMULAS[side + " Warning"] = f"min(1,max(0,{blink}))"


class Scene:
    def __init__(self, vehicle=DEFAULT_VEHICLE):
        self.assets = vehicle_assets(vehicle)
        self.document = ET.Element("Rive", version="1", kind="fragment")
        self.serial = 100
        self.converters = {}
        self.animation_keys = []

    def ident(self):
        self.serial += 1
        return f"0:{self.serial}"

    def el(self, parent, element_type, **attrs):
        return ET.SubElement(parent, element_type, {key: str(value).lower() if isinstance(value, bool)
                                         else str(value) for key, value in attrs.items()})

    def bind(self, parent, prop, key, converter=None):
        attrs = dict(sourcePathIds=f"1:1-{IDS[prop]}", propertyKey=key)
        if converter:
            attrs["converterId"] = converter
        return self.el(parent, "DataBindContext", **attrs)

    def formula(self, name, expression):
        if name in self.converters:
            return self.converters[name]
        identity = self.ident()
        converter = self.el(self.document, "DataConverterFormula", name=name, id=identity)
        self.tokens(converter, ast.parse(expression, mode="eval").body)
        self.converters[name] = identity
        return identity

    def tokens(self, parent, node):
        if isinstance(node, ast.Constant):
            self.el(parent, "FormulaTokenValue", operationValue=node.value)
        elif isinstance(node, ast.Name):
            if node.id == "input":
                self.el(parent, "FormulaTokenInput")
            else:
                token = self.el(parent, "FormulaTokenValue")
                converter = "2:3" if PROPERTIES[node.id][0] == "Boolean" else None
                self.bind(token, node.id, 777, converter)
        elif isinstance(node, ast.BinOp):
            self.el(parent, "FormulaTokenParenthesisOpen")
            self.tokens(parent, node.left)
            self.el(parent, "FormulaTokenOperation", operationType={
                ast.Add: 0, ast.Sub: 1, ast.Mult: 2, ast.Div: 3, ast.Mod: 4}[type(node.op)])
            self.tokens(parent, node.right)
            self.el(parent, "FormulaTokenParenthesisClose")
        elif isinstance(node, ast.Call):
            self.el(parent, "FormulaTokenFunction", functionType={
                "min": 0, "max": 1, "round": 2, "floor": 4, "sqrt": 5, "pow": 6}[node.func.id])
            for index, arg in enumerate(node.args):
                if index:
                    self.el(parent, "FormulaTokenArgumentSeparator")
                self.tokens(parent, arg)
            self.el(parent, "FormulaTokenParenthesisClose")
        else:
            raise ValueError(ast.dump(node))

    def opacity(self, parent, prop, expression, name):
        # Use the converter's input for the triggering property, not a second
        # external binding back to the same value.
        expression = expression.replace(prop, "input")
        converter = self.formula(name, expression)
        if PROPERTIES[prop][0] == "Boolean":
            converter = self.chain(name + " typed boolean", "2:3", converter)
        self.bind(parent, prop, 18, converter)

    def node(self, parent, name, x=0, y=0, **attrs):
        return self.el(parent, "Node", name=name, x=x, y=y, id=self.ident(), **attrs)

    def image(self, parent, name, asset, x, y):
        return self.el(parent, "Image", name=name, assetId=IMAGE_IDS[asset],
                       x=x, y=y, id=self.ident(), samplerFilter="bilinear")

    def theme_color(self, solid, dark, light):
        for key,offset in ((118,2),(136,4),(210,6)):
            dark_channel=int(dark[offset:offset+2],16)
            light_channel=int(light[offset:offset+2],16)
            formula=self.formula(f'Theme channel {dark_channel} {light_channel}',
                                 f'{light_channel}+({dark_channel}-{light_channel})*input')
            self.bind(solid,'darkMode',key,self.chain(
                f'Theme boolean channel {dark_channel} {light_channel}','2:3',formula))

    def paint(self, parent, color, stroke=0, light=None):
        p = self.el(parent, "Stroke" if stroke else "Fill", name="Paint",
                    **({"thickness": stroke, "cap": "round", "join": "round"} if stroke else {}))
        # Match the authored/static preview to the default theme as well as
        # the runtime VM. A viewer may show art before advancing bindings.
        initial=light if light and not PROPERTIES['darkMode'][1] else color
        solid=self.el(p, "SolidColor", colorValue=initial, name="Color")
        if light:
            self.theme_color(solid,color,light)

    def rect(self, parent, name, x, y, width, height, color, radius=0, light=None, **attrs):
        shape = self.el(parent, "Shape", name=name, x=x, y=y, id=self.ident())
        path = self.el(shape, "Rectangle", name="Outline", width=width, height=height,
                       cornerRadiusTL=radius, id=self.ident(), **attrs)
        self.paint(shape, color, light=light)
        return path

    def ellipse(self, parent, name, x, y, width, height, color, stroke=0, light=None):
        shape = self.el(parent, "Shape", name=name, x=x, y=y, id=self.ident())
        self.el(shape, "Ellipse", name="Outline", width=width, height=height)
        self.paint(shape, color, stroke, light=light)
        return shape

    def polygon(self, parent, name, points, color, stroke=0, closed=True, light=None):
        shape = self.el(parent, "Shape", name=name, id=self.ident())
        path = self.el(shape, "PointsPath", name="Outline", isClosed=closed)
        vertices = [self.el(path, "StraightVertex", x=x, y=y, radius=3, id=self.ident())
                    for x, y in points]
        self.paint(shape, color, stroke, light=light)
        return vertices

    def text(self, parent, name, value, x, y, width, height, size, color="FFF4F7FA", bold=False,
             prop=None, converter="2:1", align="left", light=None):
        text = self.el(parent, "Text", name=name, x=x, y=y, width=width, height=height,
                       sizingValue="fixed", alignValue=align, verticalAlignValue="middle",
                       wrapValue="noWrap", overflowValue="fitFontSize", id=self.ident())
        identity = self.ident()
        style = self.el(text, "TextStylePaint", fontSize=size, fontAssetId="2:901" if bold else "2:900",
                        familyName="Montserrat", styleName="Bold" if bold else "Light", name="Typography", id=identity)
        self.paint(style, color, light=light)
        self.el(style, "TextStyleFeature", tag=1953396077, featureValue=1, name="Tabular figures")
        run = self.el(text, "TextValueRun", styleId=identity, text=value, name="Value")
        if prop:
            self.bind(run, prop, 268, converter)
        return text

    def layout(self, parent, name, width=0, height=0, fill_w=False, fill_h=False, **attrs):
        identity, style_id = self.ident(), self.ident()
        box = self.el(parent, "LayoutComponent", name=name, width=width, height=height,
                      id=identity, styleId=style_id)
        self.el(box, "LayoutComponentStyle", id=style_id, name=name + " layout",
                layoutWidthScaleType="fill" if fill_w else "fixed",
                layoutHeightScaleType="fill" if fill_h else "fixed", **attrs)
        return box

    def machine(self, artboard, animation, name):
        machine_id, state = self.ident(), self.ident()
        artboard.set("defaultStateMachineId", machine_id)
        machine = self.el(artboard, "StateMachine", name=name, id=machine_id)
        layer = self.el(machine, "StateMachineLayer", name="Motion", id=self.ident())
        self.el(layer, "AnyState", x=200, y=-160)
        self.el(layer, "ExitState", x=420, y=-160)
        entry = self.el(layer, "EntryState", x=0, y=0)
        self.el(entry, "StateTransition", stateToId=state)
        self.el(layer, "AnimationState", animationId=animation, id=state, x=200, y=0)

    def build(self):
        vm = self.el(self.document, "ViewModel", name="DashViewModel", id="1:1", defaultInstanceId="1:2")
        for name, (kind, _) in PROPERTIES.items():
            self.el(vm, "ViewModelProperty" + kind, name=name, id=IDS[name])
        instance = self.el(vm, "ViewModelInstance", name="Default", id="1:2", exports=True)
        for name, (kind, value) in PROPERTIES.items():
            self.el(instance, "ViewModelInstance" + kind, propertyValue=value, viewModelPropertyId=IDS[name])
        for name, path in self.assets.items():
            self.el(self.document, "ImageAsset", file=path,
                    name=name, id=IMAGE_IDS[name])
        self.el(self.document, "FontAsset", file="fonts/Montserrat-Light.ttf", name="Montserrat Light", id="2:900")
        self.el(self.document, "FontAsset", file="fonts/Montserrat-Bold.ttf", name="Montserrat Bold", id="2:901")
        self.el(self.document, "ComponentAsset", name="Road motion", id="4:4", artboardId="4:1")
        self.el(self.document, "DataConverterToString", decimals=0, round=True, name="Integer", id="2:1")
        self.el(self.document, "DataConverterToString", name="Boolean text", id="2:2")
        self.el(self.document, "DataConverterToNumber", name="Numeric boolean", id="2:4")
        group = self.el(self.document, "DataConverterGroup", name="Boolean opacity", id="2:3")
        self.el(group, "DataConverterGroupItem", converterId="2:2")
        self.el(group, "DataConverterGroupItem", converterId="2:4")

        # Newhaven's 800 x 480 coordinate system, uniformly scaled to the
        # contest's 1080-unit height. Center artwork stays centered; peripheral
        # clusters remain edge-anchored as DashPilot resizes the artboard.
        main = self.el(self.document, "Artboard", name="Newhaven", id="3:1", width=1800, height=1080,
                       styleId="3:2", viewModelId="1:1", viewModelInstanceId="1:2", clip=True)
        self.el(main, "LayoutComponentStyle", name="Artboard layout", id="3:2")
        self.paint(main, "FF000000",light="FFFFFFFF")
        root = self.layout(main, "Newhaven composition", fill_w=True, fill_h=True,
                           flexDirectionValue="column",directionValue="ltr")
        driving = self.layout(root, "Driving region 80 percent", fill_h=True, fill_w=True,
                              flexBasis=0,flexBasisUnitsValue="points",
                              flexDirectionValue="row")
        driving.set('fractionalHeight','4')
        left = self.layout(driving, "Left edge", fill_w=True, fill_h=True, flexBasis=0, flexBasisUnitsValue="points")
        cluster = self.node(left, "Speed and power", scaleX=2.25, scaleY=2.25)
        self.opacity(cluster,"gear",f"1-({PARK})","Instruments outside Park")
        self.text(cluster, "Current speed", "130", 20,23,210,115,110, prop="egoSpeed",light="FF2D3436")
        # Each unit follows the speed's digit count, as in LVGL's label alignment.
        for label, expr in (("km/h", "1-isImperial"), ("mph", "isImperial")):
            unit = self.text(cluster, "Speed unit " + label, label, 220,95,65,25,18,"FFB8C1C5")
            self.opacity(unit, "isImperial", expr, label)
            self.bind(unit, "egoSpeed", 13, self.formula("Unit position",
                "16+min(1,max(0,input-9))*68+min(1,max(0,input-99))*68+68"))
        up = self.rect(cluster, "Consumption fill", 12.5,192,5,1,"FFB8C1C5",2,originY=1,light="FF2D3436")
        self.bind(up, "powerLevel", 21, self.formula("Power Up", FORMULAS["Power Up"]))
        down = self.rect(cluster, "Recuperation fill",12.5,192,5,1,"FF5CBD68",2,originY=0)
        self.bind(down,"powerLevel",21,self.formula("Power Down",FORMULAS["Power Down"]))
        self.rect(cluster,"Power track",12.5,192,5,288,"FF2B3236",3,light="FFECF0F1")

        center = self.layout(driving, "Road center", width=0, fill_h=True)
        scene = self.node(center, "Native 800 pixel scene", -900,0,scaleX=2.25,scaleY=2.25)
        for side,x in (("left",200),("right",600)):
            car_group = self.node(scene,side+" blind spot",x,292)
            self.opacity(car_group,side+"BlindSpot",FORMULAS[side+" Occupied"],side+" Occupied")
            warning = self.image(car_group,side+" red vehicle",side+"_red",0,0)
            self.opacity(warning,side+"Blinker",FORMULAS[side+" Warning"],side+" Warning")
            self.image(car_group,side+" grey vehicle",side+"_grey",0,0)
        park = self.image(scene,"Park front three-quarter vehicle","park",400,384)
        park.set("originY","1")
        self.opacity(park,"gear",PARK,"Park vehicle visible")
        ego = self.image(scene,"Driving ego vehicle","ego",400,234)
        self.opacity(ego,"gear",f"1-({PARK})","Driving vehicle visible")
        # A gear-gated wrapper prevents a launch cue lingering after a shift.
        # The inner node's motion/opacity belong exclusively to its timeline.
        direction_cues=[]
        for label,gear,y,direction in (("Forward",4,143,1),("Reverse",2,326,-1)):
            cue=self.node(scene,label+' stopped direction',400,y)
            self.opacity(cue,'gear',equal('gear',gear),label+' direction gear')
            moving=self.node(cue,label+' direction motion',opacity=0)
            vertices=self.polygon(moving,label+' direction arrow',direction_arrow_points(direction),
                                  'FFF4F7FA',light='FF2D3436')
            for vertex in vertices:
                vertex.set('radius','0.5')
            direction_cues.append((label,gear,direction,moving))
        for side,x in (("left",300),("right",500)):
            arrow = self.node(scene,side+" turn signal",x,42)
            vertices=self.polygon(arrow,side+" arrow geometry",
                                  turn_signal_points(side),'FF35D774')
            for vertex in vertices:
                vertex.set('radius','1.2')
            self.opacity(arrow,side+"Blinker",FORMULAS[side+" Arrow"],side+" Arrow")
        road = self.el(scene,"NestedArtboard",name="Speed driven road",id=self.ident(),artboardId="4:1")
        # A nested artboard does not play its timeline merely because it has a
        # default state machine. Explicitly start playback and bind its speed.
        travel=self.el(road,"NestedSimpleAnimation",name="Speed driven lane travel",
                       animationId="4:3",isPlaying=True)
        self.bind(travel,"egoSpeed",199,self.formula("Road Rate",ROAD_RATE))
        self.opacity(road,"gear",f"1-({PARK})","Road outside Park")

        right = self.layout(driving,"Right edge",fill_w=True,fill_h=True,layoutAlignmentType="topRight",
                            flexBasis=0,flexBasisUnitsValue="points")
        right_box = self.layout(right,"Speed limit anchor",width=270,fill_h=True)
        sign = self.node(right_box,"Known speed limit",108,162,scaleX=2.25,scaleY=2.25)
        self.opacity(sign,"fusedSpeedLimit","min(1,max(0,input))","Limit known")
        self.text(sign,"Speed limit value","130",-40,-35,80,70,36,"FF000000",True,
                  "fusedSpeedLimit",align="center")
        self.ellipse(sign,"Sign face",0,0,76,76,"FFFFFFFF",light="FFECF0F1")
        self.ellipse(sign,"Sign red border",0,0,96,96,"FFE02020")

        footer = self.layout(root,"Invisible status region 20 percent",fill_h=True,fill_w=True,
                             flexBasis=0,flexBasisUnitsValue="points")
        footer.set('fractionalHeight','1')
        battery_col = self.layout(footer,"Battery left",fill_w=True,fill_h=True,flexBasis=0,flexBasisUnitsValue="points")
        bat = self.node(battery_col,"Known battery",54,81,scaleX=2.25,scaleY=2.25)
        self.opacity(bat,"fullPackEnergy",BATTERY_VISIBLE,"Battery Visible")
        converter = self.chain("Battery label",self.formula("Battery Percent",BATTERY),"2:1")
        label = self.node(bat,"Battery percentage label")
        self.text(label,"Battery percentage","51",58,0,35,24,18,"FFB8C1C5",
                  prop="nominalEnergyRemaining",converter=converter,light="FF2D3436")
        percent = self.text(label,"Percent sign","%",80,0,22,24,18,"FFB8C1C5",light="FF2D3436")
        self.bind(percent,"nominalEnergyRemaining",13,self.formula("Percent position",
            "58+11*(1+min(1,max(0,("+BATTERY+")-9))+min(1,max(0,("+BATTERY+")-99)))"))
        fill = self.rect(bat,"Battery charge",2,12,40,10,"FF5CBD68",1,originX=0)
        self.bind(fill,"nominalEnergyRemaining",20,self.formula("Battery width",f"({BATTERY})*0.4"))
        self.rect(bat,"Battery empty",22,12,40,10,"FF252A2D",1,light="FFECF0F1")
        self.rect(bat,"Battery frame",22,12,44,14,"FF7C8589",2)
        self.rect(bat,"Battery terminal",45.5,12,3,6,"FF7C8589",1)
        ap_col = self.layout(footer,"Autopilot center",width=0,fill_h=True)
        ap = self.image(self.node(ap_col,"Autopilot anchor",0,108,scaleX=2.025,scaleY=2.025),
                        "Autopilot","autopilot",0,0)
        self.opacity(ap,"adasOn","adasOn","Assist active")
        gear_col = self.layout(footer,"Gear right",fill_w=True,fill_h=True,layoutAlignmentType="topRight",
                               flexBasis=0,flexBasisUnitsValue="points")
        gear_box = self.layout(gear_col,"Gear anchor",width=108,fill_h=True)
        gear_node = self.node(gear_box,"Selected gear",0,76.5,scaleX=2.25,scaleY=2.25)
        for letter,value in (("P",1),("R",2),("N",3),("D",4),("—",0)):
            txt = self.text(gear_node,"Gear "+letter,letter,0,0,24,28,24,align="right",light="FF2D3436")
            self.opacity(txt,"gear",equal("gear",value),"Gear "+letter)
        machine_id=self.ident()
        main.set("defaultStateMachineId",machine_id)
        machine=self.el(main,"StateMachine",id=machine_id,name="Newhaven dashboard")
        for cue in direction_cues:
            self.direction_machine(main,machine,*cue)
        self.road_artboard()
        return self.document

    def number_condition(self,transition,prop,value,operator='equal'):
        condition=self.el(transition,'TransitionViewModelCondition',opValue=operator)
        comparator=self.el(condition,'TransitionPropertyViewModelComparator')
        self.bind(self.el(comparator,'BindablePropertyNumber'),prop,636)
        self.el(condition,'TransitionValueNumberComparator',value=value)

    def direction_machine(self,main,machine,label,gear,direction,target):
        layer=self.el(machine,'StateMachineLayer',name=label+' departure cue',id=self.ident())
        self.el(layer,'AnyState',x=0,y=-150)
        self.el(layer,'ExitState',x=600,y=-150)
        entry=self.el(layer,'EntryState',x=0,y=0)
        states={name:self.ident() for name in ('hidden','stopped','departing')}
        animations={name:self.ident() for name in states}
        self.el(entry,'StateTransition',stateToId=states['hidden'])
        nodes={name:self.el(layer,'AnimationState',id=identity,animationId=animations[name],
                            reset=True,x=200+index*200,y=0)
               for index,(name,identity) in enumerate(states.items())}

        def transition(source,destination,*conditions,**flags):
            result=self.el(nodes[source],'StateTransition',stateToId=states[destination],**flags)
            for prop,value,operator in conditions:
                self.number_condition(result,prop,value,operator)

        zero=('egoSpeed',0,'equal')
        moving=('egoSpeed',0,'notEqual')
        selected=('gear',gear,'equal')
        changed=('gear',gear,'notEqual')
        transition('hidden','stopped',zero,selected)
        transition('stopped','hidden',changed)
        transition('stopped','departing',moving,selected)
        transition('departing','hidden',changed)
        transition('departing','stopped',zero,selected)
        transition('departing','hidden',enableExitTime=True,exitTimeIsPercetange=True,exitTime=100)

        for name in states:
            animation=self.el(main,'LinearAnimation',name=label+' direction '+name,
                              id=animations[name],duration=24 if name=='departing' else 1,
                              fps=60,loopValue='oneShot')
            for key,values in ((18,((0,.30),(24,0)) if name=='departing' else
                               ((0,.30 if name=='stopped' else 0),)),
                               (14,((0,0),(24,-40*direction)) if name=='departing' else ((0,0),))):
                obj=self.el(animation,'KeyedObject',objectId=target.get('id'))
                prop=self.el(obj,'KeyedProperty',propertyKey=key)
                for frame,value in values:
                    self.el(prop,'KeyFrameDouble',frame=frame,value=value,interpolationType='linear')

    def chain(self,name,*converters):
        identity=self.ident()
        group=self.el(self.document,"DataConverterGroup",name=name,id=identity)
        for conv in converters:
            self.el(group,"DataConverterGroupItem",converterId=conv)
        return identity

    def road_artboard(self):
        road=self.el(self.document,"Artboard",name="Road motion",id="4:1",width=800,height=384,
                     clip=True,styleId="4:2",viewModelId="1:1",viewModelInstanceId="1:2",
                     isComponent=True,x=2400,y=0)
        self.el(road,"LayoutComponentStyle",name="Road layout",id="4:2")
        for color,label in (("FF0071FF","Assist lanes"),("FFD9E0E3","Neutral lanes")):
            group=self.node(road,label)
            if label=="Assist lanes":
                self.opacity(group,"adasOn","adasOn","Assist active")
            for side in (-1,1):
                # Include a clipped incoming dash so the loop never pops a new
                # marking into view at the top. One cycle is 6 m paint + 6 m gap.
                for row, (start, length) in enumerate(zip((-34,0,44,105,181,276,394),(12,17,24,33,44,58,74))):
                    y = start*384/480
                    bottom = (start+length)*384/480
                    points=[(400+side*(50+y*55/384),y),
                            (400+side*(50+bottom*55/384),bottom)]
                    vertices=self.polygon(group,f"Lane {label} {side} {row}",points,color,row+1,False,
                                          light="FFECF0F1" if label=="Neutral lanes" else None)
                    stroke=group[-1].find('Stroke')
                    stroke.set('id',self.ident())
                    self.animation_keys.append((stroke.get('id'),47,row+1,row+2))
                    for endpoint, vertex in enumerate(vertices):
                        next_start = (0,44,105,181,276,394,535)[row]
                        next_length = (17,24,33,44,58,74,90)[row]
                        end_y=(next_start+(next_length if endpoint else 0))*384/480
                        self.animation_keys.extend(((vertex.get('id'),24,points[endpoint][0],400+side*(50+end_y*55/384)),
                                                    (vertex.get('id'),25,points[endpoint][1],end_y)))
        animation=self.el(road,"LinearAnimation",name="One 12 metre road cycle",id="4:3",duration=60,fps=60,loopValue="loop")
        for identity,key,start,end in self.animation_keys:
            obj=self.el(animation,"KeyedObject",objectId=identity)
            prop=self.el(obj,"KeyedProperty",propertyKey=key)
            self.el(prop,"KeyFrameDouble",value=start,frame=0,interpolationType="linear")
            self.el(prop,"KeyFrameDouble",value=end,frame=60,interpolationType="linear")


def generate(vehicle=DEFAULT_VEHICLE):
    for path in vehicle_assets(vehicle).values():
        bundled=ROOT/path
        if not bundled.is_file():
            raise FileNotFoundError(f'Missing bundled dashboard asset: {bundled}')
    for name in ('Montserrat-Light.ttf','Montserrat-Bold.ttf','OFL.txt'):
        if not (ROOT/'fonts'/name).is_file():
            raise FileNotFoundError(f'Missing bundled font/license: {name}')
    scene=Scene(vehicle)
    tree=ET.ElementTree(scene.build())
    ET.indent(tree,space="  ")
    # Keep a conventional final newline so editors do not alter generated output.
    (ROOT/"scene.rml").write_text(
        ET.tostring(tree.getroot(),encoding="unicode") + "\n",
        encoding="utf-8", newline="\n")


if __name__ == "__main__":
    generate()
