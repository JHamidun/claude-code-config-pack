"""Original-raster mask tracing; no filesystem defaults or image mutation."""
import math
import cv2
import numpy as np
from skimage.morphology import skeletonize

def trace_paths(mask,x0,y0):
    sk=skeletonize(mask)
    dist=cv2.distanceTransform(mask.astype(np.uint8),cv2.DIST_L2,5)
    nodes={(int(x),int(y)) for y,x in np.argwhere(sk)}
    def adjacent(p):
        x,y=p;result=[]
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
            q=x+dx,y+dy
            if q not in nodes:continue
            if dx and dy and ((x+dx,y) in nodes or (x,y+dy) in nodes):continue
            result.append(q)
        return result
    graph={p:adjacent(p) for p in nodes}
    used=set();paths=[]
    def edge(a,b):return tuple(sorted([a,b]))
    def walk(start,nextp):
        path=[start];previous,current=start,nextp
        used.add(edge(start,nextp))
        while True:
            path.append(current)
            options=[p for p in graph[current] if edge(current,p) not in used]
            if not options or len(graph[current])!=2:break
            n=options[0];used.add(edge(current,n));previous,current=current,n
        return path
    for p in sorted(nodes,key=lambda a:(a[1],a[0])):
        if len(graph[p])!=2:
            for q in graph[p]:
                if edge(p,q) not in used:paths.append(walk(p,q))
            if not graph[p]:paths.append([p,p])
    for p in sorted(nodes):
        for q in graph[p]:
            if edge(p,q) not in used:paths.append(walk(p,q))
    result=[]
    for p in paths:
        points=np.array(p,dtype=np.float32)
        length=float(np.linalg.norm(np.diff(points,axis=0),axis=1).sum())
        if length<1.4:continue
        radius=max(float(dist[y,x]) for x,y in p)
        simple=cv2.approxPolyDP(points.reshape(-1,1,2),.65,False).reshape(-1,2)
        if len(simple)<2:continue
        result.append({'points':[[round(float(x+x0),2),round(float(y+y0),2)] for x,y in simple],
                       'width':round(radius*2+5,2),'length':round(length,2)})
    # Long contour strokes establish the object, shorter hatch/detail strokes follow.
    result.sort(key=lambda p:(-int(p['length']>=45),-p['length']))
    return result


def color_paths(mask,x0,y0):
    # Narrow diagonal strokes color the existing illustration like a highlighter.
    h,w=mask.shape;result=[]
    for d in range(-h,w,11):
        active=[]
        for y in range(h-1,-1,-1):
            x=d+h-1-y
            if 0<=x<w and mask[y,x]:active.append((x,y))
            elif active:
                if len(active)>2:
                    a,b=active[0],active[-1]
                    result.append({'points':[[a[0]+x0,a[1]+y0],[b[0]+x0,b[1]+y0]],'width':17,
                                   'length':round(math.dist(a,b),2)})
                active=[]
        if len(active)>2:
            a,b=active[0],active[-1]
            result.append({'points':[[a[0]+x0,a[1]+y0],[b[0]+x0,b[1]+y0]],'width':17,'length':round(math.dist(a,b),2)})
    return result


def order_strokes(paths, lettering=False):
    """Keep related strokes spatially close instead of jumping across the drawing."""
    if lettering:
        paths.sort(key=lambda p:(int(min(x for x,y in p['points'])//25),-p['length']))
        return paths
    remaining=list(paths);result=[];cursor=None
    while remaining:
        long=[p for p in remaining if p['length']>=45]
        candidates=long or remaining
        if cursor is None:
            selected=max(candidates,key=lambda p:p['length'])
        else:
            selected=min(candidates,key=lambda p:min(math.dist(cursor,p['points'][0]),math.dist(cursor,p['points'][-1])))
            if math.dist(cursor,selected['points'][-1])<math.dist(cursor,selected['points'][0]):
                selected['points'].reverse()
        remaining.remove(selected);result.append(selected);cursor=selected['points'][-1]
    return result


