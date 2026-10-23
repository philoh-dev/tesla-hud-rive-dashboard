"""Share ground-space samples across lane corners and visual layers."""

ROWS=16


def sample_name(row,endpoint,quantity):
    return f'_laneSample{row}_{endpoint}_{quantity}'


SAMPLE_DEFAULTS={sample_name(row,end,quantity):value
                 for row in range(ROWS) for end in (0,1)
                 for quantity,value in (('Depth',min(186,6+row*12+end*6)),
                                        ('Center',0),('Slope',0),('InvNormal',1))}


def add_projection_cache(scene,road):
    from myj_projection import (NEAR_Z,FAR_Z,CYCLE_LENGTH,PAINT_LENGTH,
                                ground_curve_expression,ground_slope_expression)
    for row in range(ROWS):
        for end in (0,1):
            names={q:sample_name(row,end,q) for q in ('Depth','Center','Slope','InvNormal')}
            depth=f'min({FAR_Z},max({NEAR_Z},{NEAR_Z+row*CYCLE_LENGTH+end*PAINT_LENGTH}-{CYCLE_LENGTH}*input))'
            values=((13,'Depth','_roadPhase',depth),
                    (14,'Center',names['Depth'],ground_curve_expression('input')),
                    (15,'Slope',names['Depth'],ground_slope_expression('input','_roadBend')),
                    (16,'InvNormal',names['Slope'],'1/sqrt(1+pow(input,2))'))
            node=scene.node(road,f'Shared road sample {row} {end}',
                            x=SAMPLE_DEFAULTS[names['Depth']],y=0,rotation=0,scaleX=1)
            for key,quantity,source,expression in values:
                scene.bind(node,source,key,scene.formula(names[quantity],expression))
                scene.bind(node,names[quantity],key).set('direction','true')


def projected_corner_expressions(row,endpoint,offset):
    from myj_projection import FOCAL,HORIZON,DEPTH_SCALE
    center=sample_name(row,endpoint,'Center')
    slope=sample_name(row,endpoint,'Slope')
    normal=sample_name(row,endpoint,'InvNormal')
    depth=f'(input-({offset})*{slope}*{normal})'
    return (f'400+{FOCAL}*({center}+({offset})*{normal})/{depth}',
            f'{HORIZON}+{DEPTH_SCALE}/{depth}')
