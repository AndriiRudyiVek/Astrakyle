"""Render the GitHub dark-theme close-up banner. Requires Pillow and numpy.
Run: python scripts/render_neural_satellite.py
Illustrative neural activity and motion; not simulation output.
"""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT=Path(__file__).resolve().parents[1]
W,H,S,N=960,480,2,144
OUT=ROOT/'docs/figures/astrakyle-neural-satellite.gif'
# Computed CSS tokens from github.com/AndriiRudyiVek/Astrakyle (2026-10-18).
BG=(13,17,23)          # --bgColor-default: #0d1117
SURFACE=(21,27,35)     # --bgColor-muted: #151b23
TEXT=(240,246,252)     # --fgColor-default: #f0f6fc
MUTED=(145,152,161)    # --fgColor-muted: #9198a1
BORDER=(61,68,77)      # --borderColor-default: #3d444d
ACCENT=(68,147,248)    # --fgColor-accent: #4493f8

def font(size,bold=False):
    candidates = ['/System/Library/Fonts/Supplemental/Arial'+(' Bold' if bold else '')+'.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf']
    for p in candidates:
        if Path(p).exists(): return ImageFont.truetype(p,size*S)
    return ImageFont.load_default(size=size*S)

y,x=np.mgrid[:H*S,:W*S]; x=x/S; y=y/S
# A planet much larger than the frame: only its curved limb is visible.
cx,cy,r=790,1080,790
dist=np.sqrt((x-cx)**2+(y-cy)**2)
inside=dist<r
z=np.sqrt(np.maximum(0,1-(dist/r)**2))
light=np.clip(.8*(cy-y)/r-.3*(x-cx)/r+.2*z,0,1)
grain=np.random.default_rng(19).normal(0,.8,x.shape)
cloud=(np.sin(x*.021+y*.009)+np.sin(x*.009-y*.035)+np.sin(x*.046+y*.023))/3
# Blend the cropped planet into the exact page background, without warm tint.
fade=np.clip((x-350)/200,0,1)
amount=np.where(inside,(.18+light*.36+cloud*.045+grain*.004),0)
amount+=np.exp(-((dist-r)/4)**2)*.60
amount=np.clip(amount*fade,0,1)
base=np.array(BG)+(np.array(BORDER)-np.array(BG))*amount[:,:,None]
base=Image.fromarray(np.clip(base,0,255).astype('uint8')).convert('RGBA')
d=ImageDraw.Draw(base)
for text,px,py,size,bold,color in [
 ('A S T R A K Y L E',42,65,13,True,ACCENT),
 ('Connection',40,112,44,True,TEXT),
 ('in motion.',40,164,44,True,TEXT),
 ('Exploring adaptive satellite',43,242,18,False,MUTED),
 ('communications through AI.',43,270,18,False,MUTED),
 ('ORBIT  /  CONNECT  /  ADAPT',43,346,12,True,MUTED),
 ('CONCEPT VISUAL · NOT TO SCALE',43,442,10,False,MUTED)]:
 d.text((px*S,py*S),text,font=font(size,bold),fill=color)
d.line((43*S,323*S,105*S,323*S),fill=ACCENT,width=2*S)
frames=[]
for i in range(N):
 t=i/N
 # Smooth periodic drift and a gradual reveal/return, with no loop jump.
 driftx=17*math.sin(2*math.pi*t); drifty=8*math.cos(2*math.pi*t)
 reveal=((1-math.cos(2*math.pi*t))/2)**1.7
 center=(696+driftx,204+drifty)
 angle=-.13+.025*math.sin(2*math.pi*t)
 layer=Image.new('RGBA',base.size); draw=ImageDraw.Draw(layer)
 def pt(p):
  a,b=p; return ((center[0]+a*math.cos(angle)-b*math.sin(angle))*S,(center[1]+a*math.sin(angle)+b*math.cos(angle))*S)
 def poly(points,fill,outline=None,width=1):
  ps=[pt(p) for p in points]; draw.polygon(ps,fill=fill)
  if outline: draw.line(ps+[ps[0]],fill=outline,width=max(1,int(width*S)),joint='curve')
 def line(points,color,width=1): draw.line([pt(p) for p in points],fill=color,width=max(1,int(width*S)))
 def dot(p,r,color):
  a,b=pt(p); draw.ellipse((a-r*S,b-r*S,a+r*S,b+r*S),fill=color)
 # Broad segmented solar arrays, foreshortened in perspective.
 for side in [-1,1]:
  def panel(a,b): return (side*a,b)
  poly([panel(49,-24),panel(171,-39),panel(177,28),panel(49,40)],(*SURFACE,255),(*MUTED,255),1.3)
  for k in range(1,7):
   a=49+k*128/7
   line([panel(a,-24-(a-49)*15/122),panel(a,40-(a-49)*12/128)],(*BORDER,255),.7)
  for k in (1,2):
   line([panel(49,-24+k*64/3),panel(174,-39+k*67/3)],(*BORDER,255),.7)
  line([panel(34,7),panel(55,7)],(*MUTED,255),3)
 # Body facets dissolve; edges remain as an x-ray shell.
 opacity=int(255*(1-.91*reveal))
 poly([(-41,-40),(25,-40),(45,-22),(45,43),(-20,47),(-41,26)],(*BORDER,opacity))
 poly([(-41,-40),(25,-40),(45,-22),(-20,-18)],(*TEXT,opacity))
 poly([(-41,-40),(-20,-18),(-20,47),(-41,26)],(*MUTED,opacity))
 # Fully connected small neural layers inside the translucent bus.
 nodes=[ [(-24,-11),(-24,8),(-24,27)], [(0,-8),(0,12),(0,32)], [(26,0),(26,23)] ]
 neural=Image.new('RGBA',base.size); nd=ImageDraw.Draw(neural)
 for k in range(2):
  for a,p in enumerate(nodes[k]):
   for b,q in enumerate(nodes[k+1]):
    alpha=int(105*reveal)
    nd.line([pt(p),pt(q)],fill=(*ACCENT,alpha),width=S)
    phase=(t*4+a*.21+b*.17+k*.3)%1
    loc=(p[0]+(q[0]-p[0])*phase,p[1]+(q[1]-p[1])*phase)
    u,v=pt(loc); rad=1.6*S
    nd.ellipse((u-rad,v-rad,u+rad,v+rad),fill=(*TEXT,int(255*reveal)))
 for k,row in enumerate(nodes):
  for j,p in enumerate(row):
   u,v=pt(p); rad=(2.5+.6*math.sin(t*8*math.pi+j+k))*S
   nd.ellipse((u-rad,v-rad,u+rad,v+rad),fill=(*ACCENT,int(255*reveal)))
 layer=Image.alpha_composite(layer,neural.filter(ImageFilter.GaussianBlur(3*S)))
 layer=Image.alpha_composite(layer,neural); draw=ImageDraw.Draw(layer)
 edge=(*MUTED,int(230-65*reveal))
 line([(-41,-40),(25,-40),(45,-22),(45,43),(-20,47),(-41,26),(-41,-40)],edge,1.3)
 line([(-41,-40),(-20,-18),(45,-22)],edge)
 line([(-20,-18),(-20,47)],edge)
 # Antenna mast, dish and cool-gray thermal trim.
 line([(5,-38),(8,-63)],(*MUTED,255),2)
 poly([(-8,-66),(8,-71),(26,-61),(8,-57)],(*BORDER,255),(*TEXT,255))
 line([(8,-63),(14,-79)],(*MUTED,255),1)
 dot((14,-79),1.7,(*TEXT,255))
 frame=Image.alpha_composite(base,layer).convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
 frames.append(frame)
# Palette from opaque and transparent phases preserves the neural highlights.
sample=Image.new('RGB',(W,H*2)); sample.paste(frames[0]);sample.paste(frames[N//2],(0,H))
palette=sample.quantize(colors=154)
colors=palette.getpalette()[:154*3]
for color in (BG,SURFACE,TEXT,MUTED,BORDER,ACCENT): colors.extend(color)
colors.extend(list(BG)*(256-len(colors)//3))
palette.putpalette(colors)
indexed=[]
for frame in frames:
    quantized=frame.quantize(palette=palette,dither=Image.Dither.NONE)
    # Pillow's palette lookup can approximate close colors; pin the flat backdrop.
    exact_bg=np.all(np.asarray(frame)==BG,axis=2)
    pixels=np.array(quantized)
    pixels[exact_bg]=154
    fixed=Image.fromarray(pixels)
    fixed.putpalette(palette.getpalette())
    indexed.append(fixed)
frames=indexed
frames[0].save(OUT,save_all=True,append_images=frames[1:],duration=100,loop=0,disposal=1,optimize=True)
print(f'{OUT}: {OUT.stat().st_size/1024/1024:.2f} MiB; 14.4-second loop')
preview=Image.new('RGB',(W,H*2))
for k,n in enumerate([0,N//2]): preview.paste(frames[n].convert('RGB'),(0,k*H))
preview.save('/tmp/astrakyle-neural-preview.png')
