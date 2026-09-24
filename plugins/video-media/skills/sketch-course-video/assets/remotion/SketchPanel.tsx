import React, {useEffect, useState} from 'react';
import {cancelRender, continueRender, delayRender, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

type Point = number[];
type Trace = {points:Point[]; width:number; start:number; duration:number; color:boolean};
type Art = {source:string; crop:number[]; dest:number[]; start:number; duration:number;
  name:string; pen:boolean; until:number|null; paths:Trace[]; finish:string; sourceWidth:number; sourceHeight:number};
type Label = {value:string; x:number; y:number; start:number; size:number; accent:boolean;
  until:number|null; heading:boolean; align?:'center'|'left'};
// Optional: large multi-line headlines for vertical stories. Absent = the lesson header, unchanged.
type TitleLayout = {size:number; y:number; align?:'center'|'left'; x?:number; lineGap?:number;
  subtitleSize?:number; subtitleGap?:number; underline?:boolean};
export type Scene = {id:string; theme:string; title:string; subtitle:string; width:number; height:number;
  assetRoot:string; palette?:{background:string; ink:string; muted:string; accent:string}; arts:Art[]; labels:Label[];
  titleLayout?:TitleLayout};
const clamp=(n:number)=>Math.max(0,Math.min(1,n));
const pace=(p:number)=>p+.021*Math.sin(p*Math.PI*2);
const d=(points:Point[])=>points.map((p,i)=>`${i?'L':'M'}${p[0]} ${p[1]}`).join(' ');

function pointOn(points:Point[],fraction:number){
  const lengths=points.slice(1).map((p,i)=>Math.hypot(p[0]-points[i][0],p[1]-points[i][1]));
  let rest=lengths.reduce((a,b)=>a+b,0)*fraction;
  for(let i=0;i<lengths.length;i++){
    if(rest<=lengths[i]){
      const k=rest/(lengths[i]||1);
      return [points[i][0]+(points[i+1][0]-points[i][0])*k,points[i][1]+(points[i+1][1]-points[i][1])*k];
    }
    rest-=lengths[i];
  }
  return points[points.length-1];
}

// accent: the scene palette accent when one is set (e.g. coral for a red/orange style);
// without a palette the marker keeps its original yellow tip and band.
function Pen({x,y,yellow,accent}:{x:number;y:number;yellow:boolean;accent?:string}){
  return <g transform={`translate(${x} ${y}) rotate(-44) scale(.85)`}>
    <path d="M3 6 L78 6 Q85 6 85 14 L85 27 Q85 32 77 32 L18 32 Z" fill="#000" opacity={.15}/>
    <path d="M0 0 L17 -8 L99 -8 Q111 -8 111 3 L111 8 Q111 17 100 17 L17 17 Z" fill="#252525" stroke="#727272" strokeWidth={1.5}/>
    <path d="M3 1 L18 -4 L18 13 L3 6 Z" fill={yellow?(accent??'#E9B714'):'#1B1A17'}/>
    <path d="M21 -6 L81 -6 L81 15 L21 15 Z" fill="#E9E5D9"/>
    <path d="M82 -7 L88 -7 L88 16 L82 16 Z" fill={yellow?(accent??'#F4C820'):'#797875'}/>
    <path d="M26 -2 L76 -2" fill="none" stroke="#FFF" strokeWidth={2} opacity={.75}/>
    <path d="M94 -3 L103 -3 Q107 -3 107 2" fill="none" stroke="#666" strokeWidth={2}/>
  </g>;
}

function RasterArt({item,t,id,assetRoot,accent}:{item:Art;t:number;id:string;assetRoot:string;accent?:string}){
  const u=(t-item.start)/item.duration;
  if(u<0 || (item.until!==null&&t>=item.until)) return null;
  const [x,y,w,h]=item.crop;
  const [dx,dy,dw,dh]=item.dest;
  const alpha=item.until!==null?clamp((item.until-t)/.32):1;
  const live=u<1?item.paths.find(p=>u>=p.start&&u<p.start+p.duration):undefined;
  const point=live?pointOn(live.points,pace(clamp((u-live.start)/live.duration))):null;
  // The completed silhouette replaces thousands of tiny stroke nodes after the reveal.
  const complete=u>=1.08;
  return <g opacity={alpha}>
    <svg x={dx} y={dy} width={dw} height={dh} viewBox={`${x} ${y} ${w} ${h}`} overflow="visible">
      <defs>
        <mask id={id} maskUnits="userSpaceOnUse" x={x-12} y={y-12} width={w+24} height={h+24}>
          {!complete&&item.paths.map((stroke,i)=>{
            const p=pace(clamp((u-stroke.start)/stroke.duration));
            return p>0?<path key={i} d={d(stroke.points)} stroke="white" fill="none" strokeWidth={stroke.width}
              strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1-p}/>:null;
          })}
          <path d={item.finish} fill="white" opacity={clamp((u-1)/.08)}/>
        </mask>
      </defs>
      <image href={staticFile(`${assetRoot}/${item.source}.png`)} width={item.sourceWidth} height={item.sourceHeight} mask={`url(#${id})`}/>
    </svg>
    {item.pen&&point&&live&&<Pen x={dx+(point[0]-x)*dw/w} y={dy+(point[1]-y)*dh/h} yellow={live.color} accent={accent}/>}
  </g>;
}

function TitleBlock({data,layout,ink,muted,accent,t}:{data:Scene;layout:TitleLayout;ink:string;muted:string;accent:string;t:number}){
  const left=layout.align==='left';
  const x=left?(layout.x??72):data.width/2;
  const anchor=left?'start':'middle';
  const gap=layout.lineGap??Math.round(layout.size*1.08);
  const lines=data.title?data.title.split('\n'):[];
  const underY=layout.y+gap*Math.max(0,lines.length-1)+Math.round(layout.size*.30);
  const x0=left?x:data.width*.25;
  const x1=left?x+Math.min(data.width-2*x,data.width*.62):data.width*.75;
  const drawn=clamp((t-.08)/.70);
  const sub=data.subtitle?data.subtitle.split('\n'):[];
  const subSize=layout.subtitleSize??Math.round(layout.size*.46);
  const subY=underY+(layout.subtitleGap??Math.round(layout.size*.95));
  return <>
    {lines.length>0&&<text x={x} y={layout.y} fill={ink} textAnchor={anchor} fontFamily="SketchHeading" fontSize={layout.size}>
      {lines.map((line,i)=><tspan key={i} x={x} dy={i?gap:0}>{line}</tspan>)}</text>}
    {lines.length>0&&layout.underline!==false&&<path d={`M${x0} ${underY} Q${(x0+x1)/2} ${underY-8} ${x1} ${underY-1}`} stroke={accent}
      strokeWidth={Math.max(6,Math.round(layout.size*.09))} strokeLinecap="round" fill="none" pathLength={1} strokeDasharray={1} strokeDashoffset={1-drawn}/>}
    {sub.length>0&&<text x={x} y={subY} fill={muted} textAnchor={anchor} fontFamily="SketchHeading" fontSize={subSize}>
      {sub.map((line,i)=><tspan key={i} x={x} dy={i?Math.round(subSize*1.25):0}>{line}</tspan>)}</text>}
  </>;
}

export function SketchPanel({data}:{data:Scene}){
  const {fps}=useVideoConfig();
  const t=useCurrentFrame()/fps;
  const dark=data.theme==='dark';
  const ink=data.palette?.ink??(dark?'#F7F7F4':'#171713');
  const muted=data.palette?.muted??(dark?'#BBBAB4':'#69675F');
  const yellow=data.palette?.accent??(dark?'#FFD014':'#DAA400');
  const [handle]=useState(()=>delayRender('Load original artwork and Cyrillic fonts'));
  useEffect(()=>{
    const fonts=[new FontFace('SketchHeading',`url(${staticFile(`${data.assetRoot}/heading.ttf`)})`),new FontFace('SketchHand',`url(${staticFile(`${data.assetRoot}/hand.ttf`)})`)];
    const images=[...new Set(data.arts.map(a=>a.source))].map(source=>new Promise<void>((resolve,reject)=>{
      const img=new Image();img.onload=()=>resolve();img.onerror=()=>reject(new Error(`Missing ${source}`));img.src=staticFile(`${data.assetRoot}/${source}.png`);
    }));
    Promise.all([...fonts.map(font=>font.load().then(f=>{document.fonts.add(f);})),...images])
      .then(()=>continueRender(handle)).catch(error=>cancelRender(error));
  },[data,handle]);
  const titleSize=data.width<1000?43:(data.title.length>41?43:48);
  const underline=clamp((t-.08)/.70);
  return <svg width={data.width} height={data.height} viewBox={`0 0 ${data.width} ${data.height}`}
    style={{background:data.palette?.background??(dark?'#000000':'#F8F3EC')}}>
    {data.titleLayout?<TitleBlock data={data} layout={data.titleLayout} ink={ink} muted={muted} accent={yellow} t={t}/>:<>
    <text x={data.width/2} y={88} fill={ink} textAnchor="middle" fontFamily="SketchHeading" fontSize={titleSize}>{data.title}</text>
    <path d={`M${data.width*.30} 112 Q${data.width*.52} 104 ${data.width*.73} 111`} stroke={yellow} strokeWidth={7} strokeLinecap="round"
      fill="none" pathLength={1} strokeDasharray={1} strokeDashoffset={1-underline}/>
    <text x={data.width/2} y={157} fill={muted} textAnchor="middle" fontFamily="SketchHeading" fontSize={data.width<1000?23:24}>{data.subtitle}</text></>}
    {data.arts.map((item,i)=><RasterArt key={item.name} item={item} t={t} id={`${data.id}-${i}`} assetRoot={data.assetRoot} accent={data.palette?.accent}/>)}
    {data.labels.map((label,i)=>{
      const opacity=clamp((t-label.start)/.25)*(label.until!==null?clamp((label.until-t)/.32):1);
      return <text key={i} x={label.x} y={label.y} fill={label.accent?yellow:ink} textAnchor={label.align==='left'?'start':'middle'}
        opacity={opacity} fontFamily={label.heading?'SketchHeading':'SketchHand'} fontSize={label.size}>{label.value}</text>;
    })}
  </svg>;
}
