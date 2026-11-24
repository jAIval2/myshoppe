import sys, numpy as np
from PIL import Image
def L(p, f=1): 
    im=Image.open(p).convert("L")
    return np.asarray(im.resize((im.width//f, im.height//f)), float)
def pc(a, b):                      # phase correlation: shift of b relative to a
    A=np.fft.fft2(a*np.hanning(a.shape[0])[:,None]*np.hanning(a.shape[1])); B=np.fft.fft2(b*np.hanning(b.shape[0])[:,None]*np.hanning(b.shape[1]))
    R=A.conj()*B; R/=np.abs(R)+1e-9; r=np.fft.ifft2(R).real
    y,x=np.unravel_index(r.argmax(), r.shape); h,w=r.shape
    return (x if x<w//2 else x-w), (y if y<h//2 else y-h), r.max()
base, edit = sys.argv[1], sys.argv[2]
a, b = L(base), L(edit)
# global scale: search on quarter size
a4, b4 = L(base,4), L(edit,4); best=None
for s in np.arange(0.80, 1.81, 0.02):
    im=Image.fromarray(a4).resize((round(a4.shape[1]*s), round(a4.shape[0]*s)))
    z=np.asarray(im,float); H,W=b4.shape
    # place the scaled base on a canvas the size of the edit, centred, then phase-correlate
    can=np.full((H,W), z.mean()); oy,ox=(z.shape[0]-H)//2,(z.shape[1]-W)//2
    if oy>=0: zz=z[oy:oy+H, ox:ox+W] if ox>=0 else None
    else: zz=None
    if zz is None or zz.shape!=(H,W):
        y0,x0=max(0,-oy),max(0,-ox); zc=z[max(0,oy):max(0,oy)+min(H,z.shape[0]), max(0,ox):max(0,ox)+min(W,z.shape[1])]
        can[y0:y0+zc.shape[0], x0:x0+zc.shape[1]]=zc; zz=can
    dx,dy,p=pc(zz-zz.mean(), b4-b4.mean())
    if best is None or p>best[0]: best=(p,s,dx*4,dy*4)
print(f"global: scale {best[1]:.2f}  shift {best[2]:+d},{best[3]:+d} px  peak {best[0]:.3f}")
# local shifts on a grid (full size), only when the scale is ~1
if abs(best[1]-1)<0.03:
    N=256; out=[]
    for cy in range(N//2+64, a.shape[0]-N//2, 192):
        for cx in range(N//2+64, a.shape[1]-N//2, 192):
            pa=a[cy-N//2:cy+N//2, cx-N//2:cx+N//2]; pb=b[cy-N//2:cy+N//2, cx-N//2:cx+N//2]
            if pa.std()<4: continue
            dx,dy,p=pc(pa-pa.mean(), pb-pb.mean()); d=np.abs(pa-pb).mean()
            out.append((cx,cy,dx,dy,p,d))
    o=np.array(out); still=(np.abs(o[:,2])<=2)&(np.abs(o[:,3])<=2)
    print(f"blocks {len(o)}: unmoved (≤2 px) {still.mean()*100:.0f} %;  mean|diff| unmoved blocks {o[still,5].mean():.1f}, moved/changed {o[~still,5].mean() if (~still).any() else 0:.1f}")
    moved=o[~still]
    if len(moved): print("  moved/changed blocks at (x,y):", ", ".join(f"({int(x)},{int(y)}:{int(dx):+d},{int(dy):+d})" for x,y,dx,dy,_,_ in moved[:14]))
