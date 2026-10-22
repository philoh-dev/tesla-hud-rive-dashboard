"""One dashboard scene with native, live vehicle-artwork selection."""
import xml.etree.ElementTree as ET

from generate import ROOT, Scene, VEHICLES, IMAGE_IDS, vehicle_assets
from park_ground import add_park_ground
from juniper_variants import PROJECTED_JUNIPERS

UNIVERSAL_TARGET='universal-dashboard'
VEHICLE_PROPERTY='vehicleDesign'
VEHICLE_PROPERTY_ID='1:100'
FALLBACK_VEHICLE='generic-vehicle'


class UniversalScene(Scene):
    def __init__(self):
        super().__init__(FALLBACK_VEHICLE)

    def design_condition(self,transition,vehicle,operator='equal'):
        condition=self.el(transition,'TransitionViewModelCondition',opValue=operator)
        comparator=self.el(condition,'TransitionPropertyViewModelComparator')
        self.el(self.el(comparator,'BindablePropertyString'),'DataBindContext',
                sourcePathIds=f'1:1-{VEHICLE_PROPERTY_ID}',propertyKey=635)
        self.el(condition,'TransitionValueStringComparator',value=vehicle)

    def build(self):
        document=super().build()
        model=document.find("ViewModel[@name='DashViewModel']")
        self.el(model,'ViewModelPropertyString',name=VEHICLE_PROPERTY,id=VEHICLE_PROPERTY_ID)
        self.el(model.find('ViewModelInstance'),'ViewModelInstanceString',
                propertyValue=FALLBACK_VEHICLE,viewModelPropertyId=VEHICLE_PROPERTY_ID)

        image_ids={FALLBACK_VEHICLE:{'ego':IMAGE_IDS['ego'],'park':IMAGE_IDS['park']}}
        for index,vehicle in enumerate(v for v in VEHICLES if v!=FALLBACK_VEHICLE):
            image_ids[vehicle]={}
            for offset,role in enumerate(('ego','park')):
                identity=f'5:{100+index*2+offset}'
                self.el(document,'ImageAsset',id=identity,name=f'{vehicle} {role}',
                        file=vehicle_assets(vehicle)[role])
                image_ids[vehicle][role]=identity

        board=document.find("Artboard[@name='Newhaven']")
        parent=board.find(".//Node[@name='Native 800 pixel scene']")
        selections={}
        for role,label in (('park','Park front three-quarter vehicle'),('ego','Driving ego vehicle')):
            original=parent.find(f"Image[@name='{label}']")
            index=list(parent).index(original)
            solo=self.el(parent,'Solo',id=self.ident(),name=f'Vehicle {role} selector',
                         x=original.get('x'),y=original.get('y'),activeComponentId=original.get('id'))
            parent.remove(original)
            parent.remove(solo)
            parent.insert(index,solo)
            # Gear gating remains independent of model selection. Both views
            # change together, including the one currently hidden by Park.
            for binding in original.findall('DataBindContext'):
                original.remove(binding)
                solo.append(binding)
            original.set('x','0')
            original.set('y','0')
            solo.append(original)
            children={FALLBACK_VEHICLE:original.get('id')}
            for vehicle in VEHICLES:
                if vehicle==FALLBACK_VEHICLE:
                    continue
                attributes=dict(original.attrib,id=self.ident(),name=f'{vehicle} {role}',
                                assetId=image_ids[vehicle][role])
                if vehicle in PROJECTED_JUNIPERS and role=='ego':
                    from myj_projection import EGO_CHASE_SCALE, EGO_CHASE_Y
                    attributes.update(scaleX=str(EGO_CHASE_SCALE),scaleY=str(EGO_CHASE_SCALE),
                                      y=str(EGO_CHASE_Y-(234+50/2.25)))
                child=self.el(solo,'Image',**attributes)
                children[vehicle]=child.get('id')
            selections[role]=(solo,children)

        selections['ground']=add_park_ground(self,document,VEHICLES)
        machine=board.find('StateMachine')
        layer=self.el(machine,'StateMachineLayer',name='Vehicle design selection',id=self.ident())
        any_state=self.el(layer,'AnyState')
        self.el(layer,'ExitState')
        entry=self.el(layer,'EntryState')
        states={vehicle:self.ident() for vehicle in VEHICLES}
        self.el(entry,'StateTransition',stateToId=states[FALLBACK_VEHICLE])
        for vehicle in VEHICLES:
            animation_id=self.ident()
            self.el(layer,'AnimationState',id=states[vehicle],animationId=animation_id)
            animation=self.el(board,'LinearAnimation',id=animation_id,
                              name=f'Vehicle selection {vehicle}',duration=1,fps=60,loopValue='oneShot')
            for solo,children in selections.values():
                prop=self.el(self.el(animation,'KeyedObject',objectId=solo.get('id')),
                             'KeyedProperty',propertyKey=296)
                self.el(prop,'KeyFrameId',frame=0,value=children[vehicle],interpolationType='hold')
            if vehicle!=FALLBACK_VEHICLE:
                transition=self.el(any_state,'StateTransition',stateToId=states[vehicle],duration=0)
                self.design_condition(transition,vehicle)
        # Exact known slugs choose their artwork; missing, empty, generic or
        # unknown strings all resolve to the same explicit fallback state.
        fallback=self.el(any_state,'StateTransition',stateToId=states[FALLBACK_VEHICLE],duration=0)
        for vehicle in VEHICLES:
            if vehicle!=FALLBACK_VEHICLE:
                self.design_condition(fallback,vehicle,'notEqual')
        return document


def generate_universal():
    document=UniversalScene().build()
    for asset in (*document.iter('ImageAsset'),*document.iter('FontAsset')):
        if not (ROOT/asset.get('file')).is_file():
            raise FileNotFoundError(f'Missing bundled asset: {asset.get("file")}')
    ET.indent(document,space='  ')
    (ROOT/'scene.rml').write_text(ET.tostring(document,encoding='unicode')+'\n',
                                  encoding='utf-8',newline='\n')
