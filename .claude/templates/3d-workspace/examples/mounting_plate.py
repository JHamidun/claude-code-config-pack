import cadquery as cq
result = cq.Workplane('XY').box(80, 50, 6).edges('|Z').fillet(5)
result = result.faces('>Z').workplane().rect(60, 30, forConstruction=True).vertices().hole(5)
show_object(result)
