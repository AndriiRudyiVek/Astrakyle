"""Render the illustrative README orbit loop. Requires numpy and Pillow.

Run from the repository root: python scripts/render_readme_animation.py
Geometry is stylized: sizes, spacing and timing are not simulation results.
"""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/figures/astrakyle-orbits.gif'
W, H, SCALE = 960, 480, 2
CX, CY, R = 670, 237, 104
N = 120
BG = (8, 19, 33)
COLORS = [(51, 204, 191), (91, 153, 236), (141, 193, 221)]

def font(size, bold=False):
    names = (["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if bold else ["/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
    for name in names:
        if Path(name).exists():
            return ImageFont.truetype(name, size * SCALE)
    return ImageFont.load_default(size=size * SCALE)

def line(draw, pts, color, width=1):
    draw.line([(round(x*SCALE),round(y*SCALE)) for x,y in pts], fill=color, width=max(1,round(width*SCALE)))

def ellipse(draw, box, fill, outline=None, width=1):
    draw.ellipse(tuple(round(v*SCALE) for v in box), fill=fill, outline=outline, width=width*SCALE)

def orbit(a, plane):
    # Orthogonal basis vectors define three circular orbital planes.
    inc, yaw = [(0.45,0.35), (1.0,1.4), (0.85,2.5)][plane]
    x,y,z = math.cos(a), math.sin(a)*math.cos(inc), math.sin(a)*math.sin(inc)
    return np.array([x*math.cos(yaw)-y*math.sin(yaw), x*math.sin(yaw)+y*math.cos(yaw),z])*178

def project(p):
    return CX+p[0], CY-p[1]

base = Image.new('RGB',(W*SCALE,H*SCALE),BG)
d=ImageDraw.Draw(base)
rng=np.random.default_rng(7)
for x,y,b in zip(rng.integers(15,W-15,90),rng.integers(15,H-15,90),rng.integers(40,90,90)):
    ellipse(d,(x-.65,y-.65,x+.65,y+.65),(int(b*.6),int(b*.8),int(b)))
d.text((42*SCALE,65*SCALE),'A S T R A K Y L E',font=font(13,True),fill=(83,211,200))
d.text((40*SCALE,112*SCALE),'Connection',font=font(44,True),fill=(235,244,250))
d.text((40*SCALE,164*SCALE),'in motion.',font=font(44,True),fill=(235,244,250))
d.text((43*SCALE,242*SCALE),'Exploring adaptive satellite',font=font(18),fill=(157,181,201))
d.text((43*SCALE,270*SCALE),'communications through AI.',font=font(18),fill=(157,181,201))
line(d,[(43,323),(105,323)],COLORS[0],2)
d.text((43*SCALE,346*SCALE),'ORBIT  /  CONNECT  /  ADAPT',font=font(12,True),fill=(116,150,175))
d.text((43*SCALE,442*SCALE),'CONCEPT VISUAL · NOT TO SCALE',font=font(10),fill=(97,124,146))
# Soft atmosphere behind the globe.
glow=Image.new('RGB',base.size,(0,0,0)); gd=ImageDraw.Draw(glow)
ellipse(gd,(CX-R-9,CY-R-9,CX+R+9,CY+R+9),(9,51,66))
glow=glow.filter(ImageFilter.GaussianBlur(16*SCALE))
base=Image.fromarray(np.maximum(np.asarray(base),np.asarray(glow)))
# Analytic orthographic sphere with graticule, diffuse light and rim.
q=np.arange(-R*SCALE,R*SCALE+1)/SCALE
xx,yy=np.meshgrid(q/R,-q/R)
mask=xx*xx+yy*yy<=1
zz=np.sqrt(np.maximum(0,1-xx*xx-yy*yy))
lat=np.arcsin(np.clip(yy,-1,1)); lon=np.arctan2(xx,zz)
light=np.clip(-.45*xx+.45*yy+.78*zz,0,1)
frames=[]
for i in range(N):
    t=i/N
    frame=base.copy(); d=ImageDraw.Draw(frame)
    # Orbit paths are split into far and near halves for proper Earth occlusion.
    def paths(front):
        for k,color in enumerate(COLORS):
            points=[orbit(a,k) for a in np.linspace(0,2*math.pi,361)]
            for a,b in zip(points,points[1:]):
                if ((a[2]+b[2])>=0)==front:
                    c=tuple(int(v*(.46 if front else .23)) for v in color)
                    line(d,[project(a),project(b)],c,1)
    def satellites(front):
        for k,color in enumerate(COLORS):
            for j in range(3):
                a=2*math.pi*(t+j/3+k*.12)
                p=orbit(a,k)
                if (p[2]>=0)!=front: continue
                # Fading trail follows the same circular plane.
                for step in range(18):
                    aa=a-(18-step)*.014
                    pa,pb=orbit(aa,k),orbit(aa+.014,k)
                    c=tuple(int(v*(.12+.65*step/18)) for v in color)
                    line(d,[project(pa),project(pb)],c,2)
                x,y=project(p)
                ellipse(d,(x-7,y-7,x+7,y+7),tuple(int(v*.13) for v in color))
                line(d,[(x-7,y),(x+7,y)],color,2)
                d.rectangle(((x-8)*SCALE,(y-3)*SCALE,(x-4)*SCALE,(y+3)*SCALE),fill=color)
                d.rectangle(((x+4)*SCALE,(y-3)*SCALE,(x+8)*SCALE,(y+3)*SCALE),fill=color)
                ellipse(d,(x-2.5,y-2.5,x+2.5,y+2.5),(239,250,255))
    paths(False); satellites(False)
    rgb=np.zeros((*xx.shape,4),dtype=np.uint8)
    for channel,value in enumerate((18,78,108)):
        rgb[:,:,channel]=np.clip(value*(.42+.78*light)+np.power(1-zz,3)*[8,35,40][channel],0,255)
    longitude=lon+2*math.pi*t
    grid=(np.abs(np.sin(longitude*6))<.025)|(np.abs(np.sin(lat*6))<.023)
    for ch,v in enumerate((55,143,166)):
        rgb[:,:,ch]=np.where(grid & mask,v*(.6+.4*light),rgb[:,:,ch])
    rgb[:,:,3]=mask.astype(np.uint8)*255
    frame.paste(Image.fromarray(rgb),(int((CX-R)*SCALE),int((CY-R)*SCALE)),Image.fromarray(rgb[:,:,3]))
    d=ImageDraw.Draw(frame)
    ellipse(d,(CX-R,CY-R,CX+R,CY+R),None,(46,123,149))
    paths(True); satellites(True)
    frames.append(frame.resize((W,H),Image.Resampling.LANCZOS))
# A shared palette avoids color flicker between frames.
palette=frames[0].quantize(colors=128)
frames=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
OUT.parent.mkdir(parents=True,exist_ok=True)
frames[0].save(OUT,save_all=True,append_images=frames[1:],duration=80,loop=0,optimize=True,disposal=1)
print(f'{OUT}: {OUT.stat().st_size / 1024 / 1024:.2f} MiB, {N} frames, {N*.08:.1f}s loop')
