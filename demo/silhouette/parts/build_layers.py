"""StepD by parts: each look is a base layer (the garment as it stands, or without its sleeves) plus parts (sleeves, collars) that
sit on the look's anchors. Everything is written in the plate frame (the 1792 x 2389 crop of the source, x 0.6696 -> 1200 x 1600),
so a layer is placed by its box alone and the page only stacks images (builder.html).

Run from demo/, with a Python that has numpy, scipy and Pillow (the plate pipeline needs only Pillow; this tool does not):
    <python> silhouette/parts/build_layers.py            the layers into assets/layers/, the manifest assets/layers/manifest.json
    <python> silhouette/parts/build_layers.py --review   also the review sheets in review/layers/

Two kinds of part:
  own     an edit of the look's own photo that lines up with it (0 px, StepD 2.1). The part is the edit where it differs from the
          base, after the edit's tone is matched to the photo (the image tool brightens the wall 2-8 %). Exact by construction.
  placed  a part cut from ANOTHER look's edit and placed on this look (StepD 2.2, 2.3): one uniform scale and rotation fitted by
          least squares on the anchors, a bend near the join only, relit with the host's own light. Prototype quality: it needs a
          person's verdict before a customer sees it.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi

DEMO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(DEMO, "silhouette", "sources")
PEND = os.path.join(SRC, "pending")
OUT = os.path.join(DEMO, "assets", "layers")
REVIEW = os.path.join(DEMO, "review", "layers")
sys.path.insert(0, os.path.join(DEMO, "silhouette", "views"))
import torso as TK            # noqa: E402  the straight kurta's torso view: its measured edges and landmarks (source px)
import torso_anarkali as TA   # noqa: E402  the anarkali's
import torso_lehenga as TL    # noqa: E402  the lehenga choli's

W0, H0, CROP_H = 1792, 2400, 2389
FW, FH = 1200, 1600
K = FW / W0


# ---------------------------------------------------------------------------------------------------------------- loading, frame
def load_kurta(path):
    """As torso.base(), at source size: the sparkle mark covered with wall from 200 px to the left."""
    im = Image.open(path).convert("RGB")
    box = (1600, 2200, 1780, 2390)
    w, h = box[2] - box[0], box[3] - box[1]
    patch = im.crop((box[0] - 200, box[1] - 40, box[2] - 200, box[3] - 40))
    feather = Image.new("L", (w, h), 0)
    ImageDraw.Draw(feather).rectangle((12, 12, w - 12, h - 12), fill=255)
    im.paste(patch, box[:2], feather.filter(ImageFilter.GaussianBlur(6)))
    return np.asarray(im, float)


def load_anarkali(path):
    """As torso_anarkali.base(), at source size."""
    im = Image.open(path).convert("RGB")
    for (x0, y0, x1, y1), dx in TA.PATCHES:
        im.paste(im.crop((x0 + dx, y0, x1 + dx, y1)), (x0, y0))
    return np.asarray(im, float)


def load_lehenga(path):
    """As torso_lehenga.base(), at source size."""
    im = Image.open(path).convert("RGB")
    for (x0, y0, x1, y1), dx in TL.PATCHES:
        im.paste(im.crop((x0 + dx, y0, x1 + dx, y1)), (x0, y0))
    return np.asarray(im, float)


def to_frame_rgb(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).crop((0, 0, W0, CROP_H)).resize((FW, FH), Image.LANCZOS)


def to_frame_alpha(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).crop((0, 0, W0, CROP_H)).resize((FW, FH), Image.LANCZOS)


def fpt(p):
    return [round(p[0] * K, 1), round(p[1] * K, 1)]


# ---------------------------------------------------------------------------------------------------------------- image helpers
lum = lambda a: a.mean(2)                                                             # noqa: E731


def gblur(a, sig):
    """Gaussian blur at quarter size (sig in full-size px)."""
    f = 4 if sig >= 8 else 1
    if f == 1:
        return ndi.gaussian_filter(a, sig)
    h, w = a.shape
    sm = np.asarray(Image.fromarray(a.astype(np.float32), "F").resize((w // f, h // f), Image.BILINEAR), float)
    sm = ndi.gaussian_filter(sm, sig / f, mode="nearest")
    return np.asarray(Image.fromarray(sm.astype(np.float32), "F").resize((w, h), Image.BILINEAR), float)


def nblur(v, m, sig):
    """v averaged over the mask m only; also the mask's coverage."""
    a = gblur(v * m, sig)
    b = gblur(m.astype(float), sig)
    return a / np.maximum(b, 1e-4), b


def tone_match(ref, img, changed_thr=14):
    """img's tone brought to ref's outside what the edit changed: a smooth per-channel gain (the image tool's 2-8 % brightening of
    the wall). Returns the matched img and the 'unchanged' mask the gain was fitted on."""
    d0 = gblur(np.abs(ref - img).mean(2), 1.5)
    keep = ~ndi.binary_dilation(d0 > changed_thr, iterations=20)
    out = img.copy()
    for c in range(3):
        r = np.clip(ref[..., c] / np.maximum(img[..., c], 1), 0.6, 1.6)
        g1, cov = nblur(r, keep, 40)
        g2, _ = nblur(r, keep, 200)
        w = np.clip((cov - 0.1) / 0.4, 0, 1)
        out[..., c] = img[..., c] * (g1 * w + g2 * (1 - w))
    return out, keep


def clean_mask(m, min_px=1500, close=4, zone=None):
    if zone is not None:
        m = m & zone
    m = ndi.binary_opening(m, iterations=1)
    lab, n = ndi.label(m)
    if n:
        sizes = ndi.sum(m, lab, range(1, n + 1))
        m = np.isin(lab, 1 + np.nonzero(sizes >= min_px)[0])
    m = ndi.binary_closing(m, iterations=close)
    m = ndi.binary_fill_holes(m)
    if zone is not None:
        m = m & zone
    return m


def edit_distance(base, edit):
    """How far the edit is from the base: brightness, or warmth (the cloth is cooler than the wall and the form's linen)."""
    dl = np.abs(lum(base) - lum(edit))
    drb = np.abs((base[..., 0] - base[..., 2]) - (edit[..., 0] - edit[..., 2]))
    return gblur(np.maximum(dl, 1.5 * drb), 1.2)


def solid_rows(m, min_px, top_max=None):
    """Per connected piece above min_px (and, for a sleeve, starting near the shoulders: top_max): holes filled and each row filled
    between its ends (a sleeve is solid across a row; where a gap of wall is included, it is the edit's own wall, which is right)."""
    lab, n = ndi.label(m)
    out = np.zeros_like(m)
    sizes = ndi.sum(m, lab, range(1, n + 1))
    tops = ndi.minimum(np.indices(m.shape)[0], lab, range(1, n + 1))
    keep = {i + 1 for i in range(n) if sizes[i] >= min_px and (top_max is None or tops[i] <= top_max)}
    # a piece that starts lower but touches a kept piece (within 40 px) belongs to it: a shaded sleeve in a colour close to the
    # wall can come apart in two
    grown = True
    while grown and top_max is not None:
        near = set(np.unique(lab[ndi.binary_dilation(np.isin(lab, list(keep)), iterations=40)])) - {0}
        new = {i for i in near if sizes[i - 1] >= min_px} - keep
        grown = bool(new)
        keep |= new
    for i in range(1, n + 1):
        p = lab == i
        if i not in keep:
            continue
        p = ndi.binary_fill_holes(p)
        for y in np.nonzero(p.any(1))[0]:
            xs = np.nonzero(p[y])[0]
            p[y, xs.min():xs.max() + 1] = True
        out |= p
    return out


def own_part(base, edit, solid_zone, soft_zone=None, thr=11, rowfill=True, min_px=4000, grow=4, feather=1.6, top_max=None):
    """An own part: the (tone-matched) edit where it differs from the base. Solid where it differs clearly inside its zone; soft
    (alpha from the size of the difference) in the band around it, which carries the part's shadow on the garment."""
    d = edit_distance(base, edit)
    m = (d > thr) & solid_zone
    m = ndi.binary_opening(m, iterations=1)
    m = ndi.binary_closing(m, iterations=5)
    m = solid_rows(m, min_px, top_max) if rowfill else clean_mask(m, min_px=min_px)
    m = ndi.binary_dilation(m, iterations=grow) & ndi.binary_dilation(solid_zone, iterations=grow)
    a = gblur(m.astype(float), feather)
    if soft_zone is not None:
        soft = np.clip((d - 3) / 9, 0, 1) * gblur(soft_zone.astype(float), 6)
        a = np.maximum(a, gblur(soft, 2))
    return edit, a, m


# ---------------------------------------------------------------------------------------------------------------- zones (slots)
def side_lines(T, side):
    """The body line of a kurta-like view: armhole, the sleeve's inner edge to the gap, the body side; x as a function of y."""
    arm, sin, body = (T.armhole_l, T.sleeve_in_l, T.body_l) if side == "l" else (T.armhole_r, T.sleeve_in_r, T.body_r)
    ua, gap = arm[-1], body[0]
    pts = sorted(list(arm) + [p for p in sin if ua[1] <= p[1] <= gap[1]] + list(body), key=lambda p: p[1])
    ys = np.arange(H0)
    return np.interp(ys, [p[1] for p in pts], [p[0] for p in pts])


def zones_kurta():
    """The slots of the kurta's torso view (source px): each part may only change its own slot. The sleeves lie outside the body
    lines (armhole, the sleeve's inner edge, the body side: torso.py); their shadow falls in a band just inside them."""
    yy, xx = np.mgrid[0:H0, 0:W0]
    bl, br = side_lines(TK, "l"), side_lines(TK, "r")
    sh_y = min(TK.SH_L[1], TK.SH_R[1])
    rows = (yy > sh_y - 50) & (yy < 1520)
    sleeve = ((xx < bl[:, None] + 6) | (xx > br[:, None] - 6)) & rows & (xx > 250) & (xx < 1600)
    band = (((xx >= bl[:, None] + 6) & (xx < bl[:, None] + 60)) | ((xx <= br[:, None] - 6) & (xx > br[:, None] - 60))) & rows
    neck = (yy > 250) & (yy < 820) & (xx > TK.SH_L[0] + 40) & (xx < TK.SH_R[0] - 40)
    return {"sleeve": sleeve & ~neck, "sleeve_band": band & ~neck, "neck": neck}


def zones_anarkali():
    """The anarkali's slots. Its sleeves lie outside the armholes (x 685 .. 700 on the left, 1103 .. 1140 on the right:
    torso_anarkali.SEAMS) and end at the cuffs (y 1103 .. 1135); their shadow falls on the bodice just inside the armholes."""
    yy, xx = np.mgrid[0:H0, 0:W0]
    lm = TA.LM
    top = lm["shoulder-l"][1] - 45
    sleeve = (((xx > 380) & (xx < 712)) | ((xx > 1090) & (xx < 1420))) & (yy > top) & (yy < 1195)
    band = (((xx >= 712) & (xx < 770)) | ((xx > 1030) & (xx <= 1090))) & (yy > top) & (yy < 780)
    neck = (yy > 200) & (yy < 700) & (xx > 770) & (xx < 1030)
    return {"sleeve": sleeve, "sleeve_band": band, "neck": neck}


def zones_lehenga():
    """The lehenga choli's slots. Its sleeves lie outside the armholes (shoulder points x 676 / 1136, underarms x 690 / 1108:
    torso_lehenga.LM) and end at the cuffs (y 1098 .. 1128), hanging over the skirt's sides; their shadow falls on the choli just
    inside the armholes. The neckline's slot runs out to the shoulder seams above the sleeve caps (the boat neck reaches them)."""
    yy, xx = np.mgrid[0:H0, 0:W0]
    lm = TL.LM
    top = lm["shoulder-l"][1] - 45
    neck = ((yy > 200) & (yy < 600) & (xx > 712) & (xx < 1092)) | ((yy > 200) & (yy < lm["shoulder-l"][1] + 4) & (xx > 686) & (xx < 1126))
    sleeve = (((xx > 380) & (xx < 712)) | ((xx > 1092) & (xx < 1420))) & (yy > top) & (yy < 1195) & ~neck
    band = (((xx >= 712) & (xx < 770)) | ((xx > 1034) & (xx <= 1092))) & (yy > lm["shoulder-l"][1]) & (yy < 790) & ~neck
    return {"sleeve": sleeve, "sleeve_band": band, "neck": neck}


# ---------------------------------------------------------------------------------------------------------------- placement maths
def tps_fit(P, Q):
    n = len(P)
    r = np.linalg.norm(P[:, None] - P[None], axis=2)
    Km = np.where(r > 0, r * r * np.log(r + 1e-9), 0)
    Pm = np.hstack([np.ones((n, 1)), P])
    A = np.zeros((n + 3, n + 3))
    A[:n, :n] = Km + 1e-3 * np.eye(n)
    A[:n, n:] = Pm
    A[n:, :n] = Pm.T
    b = np.zeros((n + 3, 2))
    b[:n] = Q
    return np.linalg.solve(A, b), P


def tps_eval(model, X):
    w, P = model
    out = np.zeros((len(X), 2))
    for i in range(0, len(X), 100000):
        x = X[i:i + 100000]
        r = np.linalg.norm(x[:, None] - P[None], axis=2)
        U = np.where(r > 0, r * r * np.log(r + 1e-9), 0)
        out[i:i + 100000] = U @ w[:-3] + w[-3] + x @ w[-2:]
    return out


def similarity(sP, hP):
    """One uniform scale + rotation + shift, source -> host, least squares (Umeyama)."""
    mh, ms = hP.mean(0), sP.mean(0)
    X, Y = sP - ms, hP - mh
    U, D, Vt = np.linalg.svd(Y.T @ X / len(X))
    S = np.eye(2)
    if np.linalg.det(U @ Vt) < 0:
        S[1, 1] = -1
    R = U @ S @ Vt
    sc = (D * np.diag(S)).sum() / (X ** 2).sum(1).mean()
    fwd = lambda p: (sc * (R @ (p - ms).T)).T + mh                                    # noqa: E731
    inv = lambda p: ((R.T @ (p - mh).T) / sc).T + ms                                  # noqa: E731
    return fwd, inv, sc, math.degrees(math.atan2(R[1, 0], R[0, 0]))


def sampler(qx, qy, W, H):
    x0, y0 = np.floor(qx).astype(int), np.floor(qy).astype(int)
    x1, y1 = np.minimum(x0 + 1, W - 1), np.minimum(y0 + 1, H - 1)
    fx, fy = qx - x0, qy - y0

    def samp(a):
        gx, gy = fx, fy
        if a.ndim == 3:
            gx, gy = fx[..., None], fy[..., None]
        return a[y0, x0] * (1 - gx) * (1 - gy) + a[y0, x1] * gx * (1 - gy) + a[y1, x0] * (1 - gx) * gy + a[y1, x1] * gx * gy
    return samp


def edge_rows(mask, side, y0, y1, k=9):
    """The outer edge at k shares of the span y0 .. y1 (None where the row is empty)."""
    pts = []
    for t in np.linspace(0, 1, k):
        y = int(y0 + t * (y1 - y0))
        xs = np.nonzero(mask[y])[0]
        pts.append((xs.min() if side == "l" else xs.max(), y) if len(xs) else None)
    return pts


def end_centre(mask):
    ys = np.nonzero(mask.any(1))[0]
    yb = ys.max()
    xs = np.nonzero(mask[yb - 12:yb + 1].any(0))[0]
    return ((xs.min() + xs.max()) / 2, yb)


def shape_ratio(mask, side, line_x):
    """Width / height of the part outside its armhole line (StepD item 15)."""
    m = mask.copy()
    xx = np.arange(mask.shape[1])[None]
    m &= (xx <= line_x) if side == "l" else (xx >= line_x)
    ys, xs = np.nonzero(m)
    return (xs.max() - xs.min() + 1) / (ys.max() - ys.min() + 1)


# ---------------------------------------------------------------------------------------------------------------- the bell cut-out
def cut_bell(B, side):
    """The kurta's bell sleeve in its edit, cloth only: from the body line outwards, per row, the cloth-coloured pixels (the cloth is
    cooler than the wall and the form's linen: R-B small), the component that touches the shoulder; holes filled. The form's bare
    arm inside the bell's mouth is NOT part of it (the anarkali's form has no arms)."""
    e = gblur(B[..., 0] - B[..., 2], 2)
    L = gblur(lum(B), 2)
    bl = side_lines(TK, side)
    yy, xx = np.mgrid[0:H0, 0:W0]
    sh = TK.SH_L if side == "l" else TK.SH_R
    region = ((xx < bl[:, None] + 2) if side == "l" else (xx > bl[:, None] - 2)) & (yy > sh[1] - 30) & (yy < 1500)
    # the wall's colour per row, far out on that side (x 250 .. 300 left, 1560 .. 1610 right: plain wall at every sleeve row)
    ref = slice(250, 300) if side == "l" else slice(1560, 1610)
    wall_rb = np.median(e[:, ref], axis=1)[:, None]
    wall_l = np.median(L[:, ref], axis=1)[:, None]
    if side == "l":
        # the left bell is in shade: as warm as the wall but darker. From the wall inwards, the first run of 'not wall' starts
        # the sleeve; it runs to the body line. The form's bare arm in the bell's mouth is warmer than the wall: left out.
        notwall = (np.abs(L - wall_l) > 18) | (np.abs(e - wall_rb) > 7)
        m = np.zeros((H0, W0), bool)
        for y in range(int(sh[1]) - 30, 1500):
            bx = int(bl[y])
            run = np.convolve(notwall[y, 300:bx].astype(int), np.ones(5, int), "valid") == 5
            if run.any():
                m[y, 300 + int(np.argmax(run)):bx] = True
        m &= ~(e > wall_rb + 11)
    else:
        # the right bell is lit: brighter and cooler than the wall. The arm in its mouth is as warm as the wall: left out.
        m = ((e < wall_rb - 14) | (L > wall_l + 30)) & region
    m = ndi.binary_opening(m & region, iterations=2)
    lab, n = ndi.label(m)
    sizes = ndi.sum(m, lab, range(1, n + 1))
    m = lab == 1 + int(np.argmax(sizes))
    m = ndi.binary_closing(m, iterations=6)
    m = ndi.binary_fill_holes(m) & region
    # below its widest row the bell ends in its mouth; what goes on below as a narrow strip is the form's arm or the cuff: cut
    width = m.sum(1)
    yw = int(np.argmax(width))
    for y in range(yw, H0):
        if width[y] < 0.35 * width[yw]:
            m[y:] = False
            break
    return m


# ---------------------------------------------------------------------------------------------------------------- placing a sleeve
def place_sleeves(src, src_masks, src_anchor, host_O, host_N, host_masks, host_anchor, armhole_x, host_gap):
    """The prototype's place2.py as a function: each side by a uniform scale + rotation on shoulder, underarm, end and the outer
    edge to the elbow, a bend near the shoulder only, relit with the host sleeve's broad light, the host's own sleeve shadow."""
    H, W = host_N.shape[:2]
    report = {}
    Ls = lum(src)
    Lh = lum(host_O)
    gi = Image.new("L", (W, H), 0)                            # the run of wall between the hanging right sleeve and the body
    ImageDraw.Draw(gi).polygon([tuple(p) for p in host_gap], fill=255)
    gap = ndi.binary_dilation(np.asarray(gi) > 0, iterations=4)
    # under each new sleeve, the host's own sleeve cap: 55 px out from its armhole, shoulder to underarm. The sleeveless edit cut
    # the armhole further in than the sleeve's seam, and a sleeve is sewn into the seam: the cap closes the gap. Premultiplied.
    cap = np.zeros((H, W))
    for side in "lr":
        hm = host_masks[side]
        (_, shy), (_, uay) = host_anchor[side][0], host_anchor[side][1]
        for y in range(int(shy) - 15, int(uay) + 25):
            xs = np.nonzero(hm[y])[0]
            if len(xs):
                if side == "l":
                    cap[y, max(xs.max() - 55, xs.min()):xs.max() + 1] = 1
                else:
                    cap[y, xs.min():min(xs.min() + 56, xs.max() + 1)] = 1
    a_out = gblur(cap, 2.0)
    rgb_out = host_O * a_out[..., None]
    for side in "lr":
        sm, hm = src_masks[side], host_masks[side]
        hmc = ndi.binary_erosion(hm, iterations=3) & ~gap                            # the host sleeve's cloth, not the wall gap
        s_sh, s_ua, s_end = src_anchor[side]
        h_sh, h_ua, h_end = host_anchor[side]
        se = edge_rows(sm, side, s_sh[1] + 20, s_sh[1] + 0.45 * (s_end[1] - s_sh[1]))
        he = edge_rows(hm, side, h_sh[1] + 20, h_sh[1] + 0.45 * (h_end[1] - h_sh[1]))
        pairs = [(a, b) for a, b in zip(se, he) if a is not None and b is not None]
        hP = np.array([h_sh, h_ua, h_end] + [b for _, b in pairs], float)
        sP = np.array([s_sh, s_ua, s_end] + [a for a, _ in pairs], float)
        fwd, inv, sc, rot = similarity(sP, hP)
        res = sP - inv(hP)
        ax = np.array(h_end, float) - np.array(h_sh, float)
        Lx = np.linalg.norm(ax)
        u = ax / Lx
        v = np.array([-u[1], u[0]])
        zero = [np.array(h_sh) + u * Lx * t + v * d for t in (0.6, 0.8, 1.0, 1.15) for d in (-260, -130, 0, 130, 260)]
        model = tps_fit(np.vstack([hP, zero]), np.vstack([res, np.zeros((len(zero), 2))]))
        ys, xs = np.nonzero(sm)
        c = fwd(np.array([[xs.min(), ys.min()], [xs.max(), ys.min()], [xs.min(), ys.max()], [xs.max(), ys.max()]], float))
        x0, y0 = np.floor(c.min(0)).astype(int) - 80
        x1, y1 = np.ceil(c.max(0)).astype(int) + 80
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
        gy, gx = np.mgrid[y0:y1, x0:x1]
        G = np.stack([gx.ravel(), gy.ravel()], 1).astype(float)
        q = (inv(G) + tps_eval(model, G)).reshape(y1 - y0, x1 - x0, 2)
        samp = sampler(np.clip(q[..., 0], 0, W - 1), np.clip(q[..., 1], 0, H - 1), W, H)
        # relight: the part's folds over its own broad light (hard light softened), times the host sleeve's broad light
        lo_s, _ = nblur(Ls, sm, 45)
        hi = np.clip(np.where(sm, Ls / np.maximum(lo_s, 1), 1) ** 0.7, 0.75, 1.06)
        rim = 0.35 + 0.65 * np.clip(ndi.distance_transform_edt(sm) / 6, 0, 1)      # the source's shaded rim: a little of it
        hi = 1 + (hi - 1) * rim
        lo_h, cov = nblur(Lh, hmc, 45)
        lo_h2, _ = nblur(Lh, hmc, 160)
        wgt = np.clip((cov - 0.15) / 0.35, 0, 1)
        wgt = wgt * wgt * (3 - 2 * wgt)
        light = lo_h * wgt + lo_h2 * (1 - wgt)
        tint = host_O[hmc].mean(0) / Lh[hmc].mean()
        newL = light[y0:y1, x0:x1] * samp(hi)
        rgb = np.clip(newL[..., None] * tint, 0, 255)
        m_w = np.clip(samp(sm.astype(float)), 0, 1)
        a = gblur(np.clip(samp(ndi.binary_erosion(sm, iterations=3).astype(float)), 0, 1), 1.2)
        # over what is there already (the other side does not overlap)
        rgb_out[y0:y1, x0:x1] = rgb_out[y0:y1, x0:x1] * (1 - a[..., None]) + rgb * a[..., None]
        a_out[y0:y1, x0:x1] = np.maximum(a_out[y0:y1, x0:x1], a)
        placed = np.zeros((H, W), bool)
        placed[y0:y1, x0:x1] = m_w > 0.5
        r_src = shape_ratio(sm, side, src_anchor["armhole_x"][side])
        r_host = shape_ratio(placed, side, armhole_x[side])
        qa = inv(hP[:2]) + tps_eval(model, hP[:2])                                  # the join after the bend (host -> source)
        join = np.abs(qa - sP[:2]).max() * sc
        report[side] = {"scale": round(sc, 3), "rotation_deg": round(rot, 1), "shape_change_pct": round(100 * (r_host / r_src - 1), 1),
                        "bend_px": round(float(np.abs(res).max() * sc), 1), "join_px": round(float(join), 1)}
    # the sleeves' shadow on the bodice: the host's own (photo / sleeveless), above the elbow, outside the new sleeves
    ratio = np.clip(lum(host_O) / np.maximum(lum(host_N), 1), 0.55, 1.0)
    ratio = gblur(ratio, 6)
    band = np.zeros((H, W), bool)
    band[330:760, 680:1105] = True
    shade = np.where(band & ~host_masks["l"] & ~host_masks["r"], 1 - ratio, 0)
    shade = shade * (1 - a_out)
    # one RGBA: the sleeves over a black shade layer (a multiply by 'ratio' is black over at alpha 1 - ratio)
    # rgb_out is premultiplied by a_out; the shade adds black: the straight colour is rgb_out / (a_out + shade). Where nothing is,
    # the host's own sleeveless layer, so the resize to the frame does not bleed black into the edge.
    a_tot = np.clip(a_out + shade, 0, 1)
    rgb_tot = np.where(a_tot[..., None] > 1e-3, rgb_out / np.maximum(a_tot, 1e-3)[..., None], host_N)
    return np.clip(rgb_tot, 0, 255), a_tot, report


# ---------------------------------------------------------------------------------------------------------------- placing a collar
def resample(pts, k):
    pts = np.array(pts, float)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    t = np.linspace(0, d[-1], k)
    return np.stack([np.interp(t, d, pts[:, 0]), np.interp(t, d, pts[:, 1])], 1)


def place_collar(src, cm_soft, src_neck, host_O, host_neck, host_cloth_box, gar_box_src):
    """The prototype's collar.py as a function: the source's neckline onto the host's (both measured), one scale + rotation, a bend
    along the neckline only; the collar's folds times the host's light around the neck; half the source's colour cast."""
    H, W = host_O.shape[:2]
    cm = cm_soft > 0
    sP, hP = resample(src_neck, 11), resample(host_neck, 11)
    fwd, inv, sc, rot = similarity(sP, hP)
    res = sP - inv(hP)
    cx = hP[:, 0].mean()
    zero = [(cx + dx, hP[:, 1].min() - dy) for dx in (-140, -70, 0, 70, 140) for dy in (90, 60)] + \
           [(cx + dx, hP[:, 1].max() + dy) for dx in (-50, 0, 50) for dy in (170, 270, 370)]
    model = tps_fit(np.vstack([hP, zero]), np.vstack([res, np.zeros((len(zero), 2))]))
    yy, xx = np.mgrid[0:H, 0:W]
    Ls = lum(src)
    lo_s, _ = nblur(Ls, cm, 30)
    hi = np.clip(np.where(cm, Ls / np.maximum(lo_s, 1), 1) ** 0.75, 0.6, 1.0)        # folds kept, the hard light's highlights not
    x0b, y0b, x1b, y1b = host_cloth_box
    gar_h = np.zeros((H, W), bool)
    gar_h[y0b:y1b, x0b:x1b] = True
    gar_h &= lum(host_O) > 200
    hn = np.array(host_neck, float)
    ny = np.interp(xx, hn[:, 0], hn[:, 1])
    gar_h &= yy > ny + 4
    lo_h, cov = nblur(lum(host_O), gar_h, 30)
    lo_h2, _ = nblur(lum(host_O), gar_h, 120)
    wgt = np.clip((cov - 0.15) / 0.35, 0, 1)
    light = lo_h * wgt + lo_h2 * (1 - wgt)
    gx0, gy0, gx1, gy1 = gar_box_src
    gar_s = np.zeros((H, W), bool)
    gar_s[gy0:gy1, gx0:gx1] = True
    tint_s = src[gar_s].mean(0) / Ls[gar_s].mean()
    tint_h = host_O[gar_h].mean(0) / lum(host_O)[gar_h].mean()
    rel = src / np.maximum(Ls, 1)[..., None] / tint_s
    chroma = (1 + 0.5 * (rel - 1)) * tint_h
    x0, y0, x1, y1 = 650, 150, 1150, 850
    gy, gx = np.mgrid[y0:y1, x0:x1]
    G = np.stack([gx.ravel(), gy.ravel()], 1).astype(float)
    q = (inv(G) + tps_eval(model, G)).reshape(y1 - y0, x1 - x0, 2)
    samp = sampler(np.clip(q[..., 0], 0, W - 1), np.clip(q[..., 1], 0, H - 1), W, H)
    rgb = host_O.copy()                                       # outside the collar: the host (no black bleeding into the edge)
    a = np.zeros((H, W))
    rgb[y0:y1, x0:x1] = np.clip((light[y0:y1, x0:x1] * samp(hi))[..., None] * samp(chroma), 0, 255)
    a[y0:y1, x0:x1] = gblur(np.clip(samp(cm_soft), 0, 1), 0.8)
    rep = {"scale": round(sc, 3), "rotation_deg": round(rot, 1), "join_px": round(float(np.abs(res).max() * sc), 1)}
    return rgb, a, rep


# ---------------------------------------------------------------------------------------------------------------- porting a neckline
def cloth_light(O, box, neck):
    """The light on the garment's cloth around the neck, per channel: the cloth's colour (bright and cool, below the measured
    neckline) averaged over the cloth only, so a removed neck band or the form above it does not darken it."""
    H, W = O.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    n = np.array(neck, float)
    ny = np.interp(xx, n[:, 0], n[:, 1])
    x0, y0, x1, y1 = box
    cl = (yy > ny + 6) & (xx > x0) & (xx < x1) & (yy > y0) & (yy < y1)
    cl &= (lum(O) > 165) & (gblur(O[..., 0] - O[..., 2], 1.5) < 27)
    return np.stack([nblur(O[..., c], cl, 22)[0] for c in range(3)], 2), cl


def port_neck(src_O, src_E, src_alpha, src_neck, src_box, host_O, host_neck, host_box, host_top):
    """A neckline part of one look on another: the source edit warped from the source's measured neckline onto the host's (one
    scale + rotation, a bend along the neckline only), its light moved from the source's to the host's: the edit divided by the
    source's cloth light, times the host's (per channel: brightness and colour cast). The V keeps its depth in cm: both necks are
    the 158 mm of the shared scale."""
    H, W = host_O.shape[:2]
    sP, hP = resample(src_neck, 15), resample(host_neck, 15)
    fwd, inv, sc, rot = similarity(sP, hP)
    res = sP - inv(hP)
    cx, ytop, ybot = hP[:, 0].mean(), hP[:, 1].min(), hP[:, 1].max()
    span = hP[:, 0].max() - hP[:, 0].min()
    zero = [(cx + f * span, ytop - d) for f in (-0.6, -0.3, 0, 0.3, 0.6) for d in (0.45 * span, 0.3 * span)] + \
           [(cx + f * span, ybot + d) for f in (-0.8, -0.4, 0, 0.4, 0.8) for d in (0.7 * span, 1.1 * span)]
    model = tps_fit(np.vstack([hP, zero]), np.vstack([res, np.zeros((len(zero), 2))]))
    ys, xs = np.nonzero(src_alpha > 0.02)
    c = fwd(np.array([[xs.min(), ys.min()], [xs.max(), ys.min()], [xs.min(), ys.max()], [xs.max(), ys.max()]], float))
    x0, y0 = np.floor(c.min(0)).astype(int) - 40
    x1, y1 = np.ceil(c.max(0)).astype(int) + 40
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
    gy, gx = np.mgrid[y0:y1, x0:x1]
    G = np.stack([gx.ravel(), gy.ravel()], 1).astype(float)
    q = (inv(G) + tps_eval(model, G)).reshape(y1 - y0, x1 - x0, 2)
    Hs, Ws = src_E.shape[:2]
    samp = sampler(np.clip(q[..., 0], 0, Ws - 1), np.clip(q[..., 1], 0, Hs - 1), Ws, Hs)
    Ls, _ = cloth_light(src_O, src_box, src_neck)
    Lh, _ = cloth_light(host_O, host_box, host_neck)
    gain = Lh[y0:y1, x0:x1] / np.maximum(samp(Ls), 1)
    rgb = host_O.copy()
    a = np.zeros((H, W))
    out = samp(src_E) * gain
    knee = 236.0                                               # highlights: a soft shoulder, not a clip (a brighter host's gain)
    out = np.where(out > knee, knee + (255 - knee) * (1 - np.exp(-(out - knee) / (255 - knee))), out)
    rgb[y0:y1, x0:x1] = np.clip(out, 0, 255)
    a[y0:y1, x0:x1] = np.clip(samp(src_alpha), 0, 1)
    # nothing above the host's own top line (shoulder, neckline, shoulder): the V only removes cloth below it; the source's
    # shoulders slope differently and would land on the form or the wall
    t = np.array(sorted(host_top), float)
    ty = np.interp(np.arange(W), t[:, 0], t[:, 1])
    a *= np.clip((np.arange(H)[:, None] - ty[None] + 2) / 4, 0, 1)
    # the join: the host's neckline against the warped source neckline, after the bend
    qa = inv(hP) + tps_eval(model, hP)
    rep_ = {"scale": round(sc, 3), "rotation_deg": round(rot, 1), "bend_px": round(float(np.abs(res).max() * sc), 1),
            "join_px": round(float(np.abs(qa - sP).max() * sc), 1),
            "gain": [round(float(np.median(gain[..., c][samp(src_alpha) > 0.5])), 3) for c in range(3)]}
    return rgb, a, rep_


# ---------------------------------------------------------------------------------------------------------------- writing
def write_layer(name, rgb, alpha, host_dir):
    """The part in the frame, cut to its box (RGBA WebP); its box in frame px."""
    A = to_frame_alpha(alpha)
    bbox = A.point(lambda v: 255 if v > 2 else 0).getbbox()
    if bbox is None:
        raise SystemExit(f"{name}: empty layer")
    x0, y0, x1, y1 = bbox
    x0, y0, x1, y1 = max(x0 - 2, 0), max(y0 - 2, 0), min(x1 + 2, FW), min(y1 + 2, FH)
    im = to_frame_rgb(rgb).convert("RGBA")
    im.putalpha(A)
    im = im.crop((x0, y0, x1, y1))
    rel = f"assets/layers/{host_dir}/{name}.webp"
    im.save(os.path.join(DEMO, rel), quality=90, method=6)
    return {"file": rel, "box": [x0, y0, x1 - x0, y1 - y0]}


def write_base(name, rgb, host_dir):
    rel = f"assets/layers/{host_dir}/{name}.jpg"
    to_frame_rgb(rgb).save(os.path.join(DEMO, rel), quality=90, optimize=True, progressive=True)
    return rel


def overlap_px(a, b):
    return int(((a > 0.5) & (b > 0.5)).sum())


# ---------------------------------------------------------------------------------------------------------------- the build
def build(review=False):
    os.makedirs(os.path.join(OUT, "anarkali"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "straight-kurta"), exist_ok=True)
    log = []

    # ---- the straight kurta: its photo is the base; its own edits are parts (it has no sleeveless edit yet)
    KO = load_kurta(os.path.join(SRC, "torso-straight.png"))
    zk = zones_kurta()
    kb, _ = tone_match(KO, load_kurta(os.path.join(PEND, "torso-straight-sleeve-bell.png")))
    km, _ = tone_match(KO, load_kurta(os.path.join(PEND, "torso-straight-part-mandarin.png")))
    kt, _ = tone_match(KO, load_kurta(os.path.join(PEND, "torso-straight-truth-boat.png")))
    k_bell = own_part(KO, kb, zk["sleeve"], zk["sleeve_band"], top_max=max(TK.SH_L[1], TK.SH_R[1]) + 150)
    k_mand = own_part(KO, km, zk["neck"], rowfill=False, min_px=1500)
    k_boat = own_part(KO, kt, zk["neck"], rowfill=False, min_px=1500)
    for nm, (_, a, m) in {"bell": k_bell, "mandarin": k_mand, "boat": k_boat}.items():
        d_out = np.abs(KO - (kb if nm == "bell" else km if nm == "mandarin" else kt)).mean(2)[~m].mean()
        log.append(f"kurta {nm}: {int(m.sum())} px; mean |edit - photo| outside the part after the tone match {d_out:.2f} / 255")
    log.append(f"kurta overlaps (px): bell/mandarin {overlap_px(k_bell[1], k_mand[1])}, bell/boat {overlap_px(k_bell[1], k_boat[1])}")

    # ---- the anarkali: its sleeveless edit is the base; its own sleeves, the puff, and the placed parts on it
    AO = load_anarkali(os.path.join(SRC, "torso-anarkali.png"))
    za = zones_anarkali()
    AN, keep = tone_match(AO, load_anarkali(os.path.join(PEND, "torso-anarkali-under-sleeveless.png")))
    AP, _ = tone_match(AO, load_anarkali(os.path.join(SRC, "torso-anarkali-puff.png")))
    log.append(f"anarkali sleeveless: mean |edit - photo| where unchanged, after the tone match {np.abs(AO - AN).mean(2)[keep].mean():.2f} / 255")
    top = TA.LM["shoulder-l"][1] + 150
    a_full = own_part(AN, AO, za["sleeve"], za["sleeve_band"], top_max=top)
    a_puff = own_part(AN, AP, za["sleeve"], za["sleeve_band"], top_max=top)
    # the host's own sleeves, per side (for the placement's anchors and light): the full sleeve's mask, outside the armholes
    xx = np.arange(W0)[None]
    host_masks = {"l": a_full[2] & (xx <= 700), "r": a_full[2] & (xx >= 1100)}
    for s in "lr":
        hm = host_masks[s]
        lab, n = ndi.label(hm)
        sizes = ndi.sum(hm, lab, range(1, n + 1))
        host_masks[s] = ndi.binary_fill_holes(lab == 1 + int(np.argmax(sizes)))
        for y in np.nonzero(host_masks[s].any(1))[0]:
            xs = np.nonzero(host_masks[s][y])[0]
            host_masks[s][y, xs.min():xs.max() + 1] = True

    # the bell from the kurta's edit, placed on the anarkali
    KB = load_kurta(os.path.join(PEND, "torso-straight-sleeve-bell.png"))
    bell_masks = {s: cut_bell(KB, s) for s in "lr"}
    mid = lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)                          # noqa: E731
    # the anchors: shoulder point, underarm, and the wrist (the middle of the cuff of the sleeve the edit replaced: the edit lines up)
    src_anchor = {"l": (TK.SH_L, TK.UA_L, mid(TK.CUFF_OUT_L, TK.CUFF_IN_L)), "r": (TK.SH_R, TK.UA_R, mid(TK.CUFF_OUT_R, TK.CUFF_IN_R)),
                  "armhole_x": {"l": max(p[0] for p in TK.armhole_l), "r": min(p[0] for p in TK.armhole_r)}}
    lm = TA.LM
    host_anchor = {"l": (lm["shoulder-l"], lm["underarm-l"], mid(lm["cuff-out-l"], lm["cuff-in-l"])),
                   "r": (lm["shoulder-r"], lm["underarm-r"], mid(lm["cuff-out-r"], lm["cuff-in-r"]))}
    bell_rgb, bell_a, bell_rep = place_sleeves(KB, bell_masks, src_anchor, AO, AN, host_masks, host_anchor, {"l": 690, "r": 1095},
                                                TA.GAP_R)
    log.append(f"bell on anarkali: {json.dumps(bell_rep)}")

    # the mandarin from the kurta's edit, placed on the anarkali
    KM = load_kurta(os.path.join(PEND, "torso-straight-part-mandarin.png"))
    yy, xx2 = np.mgrid[0:H0, 0:W0]
    ne = np.array(TK.neck_edge, float)
    ny = np.interp(xx2, ne[:, 0], ne[:, 1])
    inx = (xx2 >= ne[:, 0].min()) & (xx2 <= ne[:, 0].max())
    below = yy - ny
    # the collar itself: what the edit changed, above the kurta's neckline (+8 px), in cloth colour (the form's linen is warmer:
    # R-B 35 .. 41 against the cloth's 17 .. 22); the front slit: a column at the centre front down to its end; nothing else the
    # edit touched (the tool also re-shaded the form's neck and the bodice beside the slit)
    rb = gblur(KM[..., 0] - KM[..., 2], 1.5)
    band = k_mand[2] & (below <= 8) & (rb < 30) & inx
    band = ndi.binary_fill_holes(ndi.binary_closing(clean_mask(band, min_px=800, close=3), iterations=3))
    slit_rows = np.nonzero((k_mand[2] & (np.abs(xx2 - TK.CF_X) < 14)).any(1))[0]
    slit = (np.abs(xx2 - TK.CF_X) < 16) & (yy >= ny - 4) & (yy <= slit_rows.max() + 6)
    raw = band | (slit & k_mand[2]) | (slit & (below <= 60))
    strip = np.where(inx & (below >= -6) & (below <= 55), np.clip((55 - below) / 32, 0, 1), 0)   # the kurta cloth under the collar
    cm_soft = np.maximum(raw.astype(float), strip)
    col_rgb, col_a, col_rep = place_collar(KM, cm_soft, TK.neck_edge, AO, TA.NECK, (760, 300, 1040, 470), (780, 440, 1020, 600))
    log.append(f"mandarin on anarkali: {json.dumps(col_rep)}")
    log.append(f"anarkali overlaps (px): bell/mandarin {overlap_px(bell_a, col_a)}, puff/mandarin {overlap_px(a_puff[1], col_a)}, "
               f"full/mandarin {overlap_px(a_full[1], col_a)}")

    # ---- the lehenga choli: its sleeveless edit is the base; every option is its own edit of its photo (all line up, 0 px)
    LO = load_lehenga(os.path.join(SRC, "torso-lehenga.png"))
    zl = zones_lehenga()
    ed = {n: tone_match(LO, load_lehenga(os.path.join(PEND, f"torso-lehenga-{n}.png")))[0]
          for n in ("under-sleeveless", "neck-v", "neck-boat", "neck-mandarin", "neck-mandarin-sleeve-short")}
    LN = ed["under-sleeveless"]
    top_l = TL.LM["shoulder-l"][1] + 150
    l_full = own_part(LN, LO, zl["sleeve"], zl["sleeve_band"], top_max=top_l)
    # the short sleeves sit on the sleeveless base, and below them the edit shows the wall the long sleeves hid in the photo: its
    # tone is matched to the base there (matched to the photo, that wall's brightness is only extrapolated)
    LS, _ = tone_match(LN, ed["neck-mandarin-sleeve-short"])
    l_short = own_part(LN, LS, zl["sleeve"], zl["sleeve_band"], top_max=top_l)                                # its sleeves only
    l_neck = {n: own_part(LO, ed[f"neck-{n}"], zl["neck"], rowfill=False, min_px=1500) for n in ("v", "boat", "mandarin")}
    keep = ~(l_full[2] | ndi.binary_dilation(zl["sleeve"], iterations=10))
    log.append(f"lehenga sleeveless: mean |edit - photo| away from the sleeves, after the tone match {np.abs(LO - LN).mean(2)[keep].mean():.2f} / 255")
    for n, (_, a, m) in l_neck.items():
        log.append(f"lehenga {n} neck: {int(m.sum())} px; mean |edit - photo| outside it {np.abs(LO - ed['neck-' + n]).mean(2)[~m].mean():.2f} / 255")
    log.append("lehenga overlaps (px): " + ", ".join(f"{sn}/{n} {overlap_px(sp[1], np_[1])}" for sn, sp in (("full", l_full), ("short", l_short))
                                                     for n, np_ in l_neck.items()))

    # ---- the lehenga's V-neck ported: onto the anarkali (the same form, stand and light) and the straight kurta (another setup)
    v_rgb, v_a, _ = l_neck["v"]
    port = {}
    a_top = [TA.LM["shoulder-l"]] + list(TA.NECK) + [TA.LM["shoulder-r"]]
    k_top = list(TK.shoulder_l) + list(TK.neck_edge) + list(TK.shoulder_r)
    for key, host_O, host_neck, host_box, host_top in (("anarkali", AO, TA.NECK, (720, 250, 1080, 700), a_top),
                                                       ("straight-kurta", KO, TK.neck_edge, (680, 330, 1110, 800), k_top)):
        prgb, pa, prep = port_neck(LO, v_rgb, v_a, TL.NECK, (720, 250, 1080, 700), host_O, host_neck, host_box, host_top)
        port[key] = (prgb, pa, prep)
        log.append(f"lehenga V-neck ported onto {key}: {json.dumps(prep)}")

    # ---- write
    L = {}
    os.makedirs(os.path.join(OUT, "lehenga"), exist_ok=True)
    L["l_base"] = write_base("base-sleeveless", LN, "lehenga")
    L["l_full"] = write_layer("sleeve-full", l_full[0], l_full[1], "lehenga")
    L["l_short"] = write_layer("sleeve-short", l_short[0], l_short[1], "lehenga")
    for n, (rgb, a, _) in l_neck.items():
        L["l_" + n] = write_layer(f"neck-{n}", rgb, a, "lehenga")
    L["k_base"] = write_base("base", KO, "straight-kurta")
    L["k_bell"] = write_layer("sleeve-bell", k_bell[0], k_bell[1], "straight-kurta")
    L["k_mand"] = write_layer("neck-mandarin", k_mand[0], k_mand[1], "straight-kurta")
    L["k_boat"] = write_layer("neck-boat", k_boat[0], k_boat[1], "straight-kurta")
    L["a_base"] = write_base("base-sleeveless", AN, "anarkali")
    L["a_full"] = write_layer("sleeve-full", a_full[0], a_full[1], "anarkali")
    L["a_puff"] = write_layer("sleeve-puff", a_puff[0], a_puff[1], "anarkali")
    L["a_bell"] = write_layer("sleeve-bell", bell_rgb, bell_a, "anarkali")
    L["a_mand"] = write_layer("neck-mandarin", col_rgb, col_a, "anarkali")

    manifest = make_manifest(L, bell_rep, col_rep)
    manifest["looks"].insert(0, lehenga_look(L))
    for key, (prgb, pa, prep) in port.items():
        lay = write_layer("neck-v-ported", prgb, pa, key)
        look = next(l for l in manifest["looks"] if l["id"] == key)
        opts = look["slots"]["neck"]["options"]
        opts[:] = [o for o in opts if o["id"] != "v"]
        opts.insert(1, {"id": "v", "name": "V neck", "sub": "Ported from the lehenga", "layer": lay, "kind": "placed",
                        "joins": ["neck-l", "cf-neck", "neck-r"],
                        "source": "the lehenga's V-neck edit, warped onto this look's measured neckline, its light moved to this photo's",
                        "fit": f"scale {prep['scale']}, rotation {prep['rotation_deg']}°, on the neckline within {prep['join_px']} px "
                               f"(bend {prep['bend_px']} px), light gain R/G/B {'/'.join(str(g) for g in prep['gain'])}"})
    thumbs(manifest)
    with open(os.path.join(OUT, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)
    with open(os.path.join(OUT, "manifest.js"), "w") as f:            # the same, for a page opened from disk (file://: no fetch)
        f.write("// written by silhouette/parts/build_layers.py: do not edit\nwindow.LAYERS = ")
        json.dump(manifest, f, indent=1, ensure_ascii=False)
        f.write(";\n")
    with open(os.path.join(OUT, "build-log.txt"), "w") as f:
        f.write("\n".join(log) + "\n")
    print("\n".join(log))
    if review:
        review_sheets(manifest)


def lehenga_look(L):
    sleeve_joins = ["shoulder-l", "underarm-l", "shoulder-r", "underarm-r"]
    neck_joins = ["neck-l", "cf-neck", "neck-r"]
    own = "the owner's {} edit of the lehenga photo"
    return {
        "id": "lehenga", "name": "Lehenga choli", "note": "Fitted crop top over a high-waisted, flared skirt",
        "base": {"file": L["l_base"], "what": "the lehenga choli without its sleeves (the owner's edit of its photo, tone-matched)"},
        "anchors": {k: fpt(v) for k, v in TL.LM.items()},
        "slots": {
            "sleeve": {"default": "full", "options": [
                {"id": "full", "name": "Full sleeves", "sub": "As photographed", "layer": L["l_full"], "kind": "own",
                 "joins": sleeve_joins, "source": "torso-lehenga.png over its sleeveless edit"},
                {"id": "short", "name": "Short sleeves", "sub": "18 cm from the shoulder", "layer": L["l_short"], "kind": "own",
                 "joins": sleeve_joins, "source": "the owner's short-sleeve edit of the lehenga photo (made with the mandarin; only its sleeves are used)"},
                {"id": "threequarter", "name": "Three-quarter", "sub": "45 cm from the shoulder", "layer": None, "kind": "missing",
                 "needs": "Its edit: prompt 8, torso-lehenga-sleeve-threequarter.png (prompt 7 with 45 cm)."},
                {"id": "sleeveless", "name": "Sleeveless", "sub": "Turned armhole edge", "layer": None, "kind": "own",
                 "joins": [], "source": "the base layer itself"}]},
            "neck": {"default": "round", "options": [
                {"id": "round", "name": "Round", "sub": "As photographed", "layer": None, "kind": "own",
                 "joins": neck_joins, "source": "the base layer itself"},
                {"id": "v", "name": "V neck", "sub": "12 cm deep", "layer": L["l_v"], "kind": "own",
                 "joins": neck_joins, "source": own.format("V-neck")},
                {"id": "boat", "name": "Boat neck", "sub": "Wide and shallow", "layer": L["l_boat"], "kind": "own",
                 "joins": neck_joins, "source": own.format("boat-neck")},
                {"id": "mandarin", "name": "Mandarin collar", "sub": "3 cm stand", "layer": L["l_mandarin"], "kind": "own",
                 "joins": neck_joins, "source": own.format("mandarin")}]}}}


def make_manifest(L, bell_rep, col_rep):
    ka = {"neck-l": TK.NECK_L, "neck-r": TK.NECK_R, "shoulder-l": TK.SH_L, "shoulder-r": TK.SH_R,
          "underarm-l": TK.UA_L, "underarm-r": TK.UA_R, "cuff-out-l": TK.CUFF_OUT_L, "cuff-in-l": TK.CUFF_IN_L,
          "cuff-out-r": TK.CUFF_OUT_R, "cuff-in-r": TK.CUFF_IN_R, "hem-l": TK.HEM_L, "hem-r": TK.HEM_R,
          "slit-l": TK.SLIT_L, "slit-r": TK.SLIT_R}
    cf = min(TK.neck_edge, key=lambda p: abs(p[0] - TK.CF_X))
    ka["cf-neck"] = cf
    aa = {k: v for k, v in TA.LM.items()}
    sleeve_joins = ["shoulder-l", "underarm-l", "shoulder-r", "underarm-r"]
    neck_joins = ["neck-l", "cf-neck", "neck-r"]

    def fit_note(rep):
        if "l" in rep:
            sh = max(abs(rep[s]["shape_change_pct"]) for s in "lr")
            rot = max(abs(rep[s]["rotation_deg"]) for s in "lr")
            jn = max(rep[s]["join_px"] for s in "lr")
            return (f"scale {rep['l']['scale']} / {rep['r']['scale']}, rotation within {rot}°, shape kept within {sh}% "
                    f"(limit 5%), shoulder and underarm joins within {jn} px")
        return f"scale {rep['scale']}, rotation {rep['rotation_deg']}°, on the measured neckline within {rep['join_px']} px"

    return {
        "frame": [FW, FH],
        "made": "silhouette/parts/build_layers.py (StepD by parts)",
        "slots": [{"id": "sleeve", "label": "Sleeves", "z": 1}, {"id": "neck", "label": "Neckline", "z": 2}],
        "looks": [
            {"id": "anarkali", "name": "Anarkali", "note": "Fitted bodice, empire seam, flared skirt with a slit",
             "base": {"file": L["a_base"], "what": "the anarkali without its sleeves (the owner's edit of its photo, tone-matched)"},
             "anchors": {k: fpt(v) for k, v in aa.items()},
             "slots": {
                 "sleeve": {"default": "full", "options": [
                     {"id": "full", "name": "Full sleeves", "sub": "As photographed", "layer": L["a_full"], "kind": "own",
                      "joins": sleeve_joins, "source": "torso-anarkali.png over its sleeveless edit"},
                     {"id": "puff", "name": "Puff sleeves", "sub": "Gathered, short", "layer": L["a_puff"], "kind": "own",
                      "joins": sleeve_joins, "source": "the owner's puff edit of the anarkali photo"},
                     {"id": "bell", "name": "Bell sleeves", "sub": "Placed from the kurta", "layer": L["a_bell"], "kind": "placed",
                      "joins": sleeve_joins, "source": "torso-straight-sleeve-bell.png, cut out and placed on the anarkali's anchors",
                      "fit": fit_note(bell_rep)},
                     {"id": "sleeveless", "name": "Sleeveless", "sub": "Turned armhole edge", "layer": None, "kind": "own",
                      "joins": [], "source": "the base layer itself"}]},
                 "neck": {"default": "round", "options": [
                     {"id": "round", "name": "Round", "sub": "As photographed", "layer": None, "kind": "own",
                      "joins": neck_joins, "source": "the base layer itself"},
                     {"id": "mandarin", "name": "Mandarin collar", "sub": "Placed from the kurta", "layer": L["a_mand"],
                      "kind": "placed", "joins": neck_joins,
                      "source": "torso-straight-part-mandarin.png, cut out and placed on the anarkali's measured neckline",
                      "fit": fit_note(col_rep)},
                     {"id": "v", "name": "V neck", "sub": "Needs an aligned edit", "layer": None, "kind": "missing",
                      "needs": "The V-neck edit came back zoomed ×1.84; it needs aligning (StepD step 3) or a fresh edit at the same framing."}]}}},
            {"id": "straight-kurta", "name": "Straight kurta", "note": "Loose straight kurta with side slits",
             "base": {"file": L["k_base"], "what": "the kurta's photo (no sleeveless edit yet)"},
             "anchors": {k: fpt(v) for k, v in ka.items()},
             "slots": {
                 "sleeve": {"default": "straight", "options": [
                     {"id": "straight", "name": "Straight sleeves", "sub": "As photographed", "layer": None, "kind": "own",
                      "joins": sleeve_joins, "source": "the base layer itself"},
                     {"id": "bell", "name": "Bell sleeves", "sub": "From the kurta's edit", "layer": L["k_bell"], "kind": "own",
                      "joins": sleeve_joins, "source": "the owner's bell edit of the kurta photo"},
                     {"id": "puff", "name": "Puff sleeves", "sub": "Needs the sleeveless kurta", "layer": None, "kind": "missing",
                      "needs": "The puff sits on the kurta without sleeves: image 1 of StepD §9 (torso-straight-under-sleeveless.png)."},
                     {"id": "sleeveless", "name": "Sleeveless", "sub": "Needs the sleeveless kurta", "layer": None, "kind": "missing",
                      "needs": "Image 1 of StepD §9 (torso-straight-under-sleeveless.png)."}]},
                 "neck": {"default": "round", "options": [
                     {"id": "round", "name": "Round", "sub": "As photographed", "layer": None, "kind": "own",
                      "joins": neck_joins, "source": "the base layer itself"},
                     {"id": "mandarin", "name": "Mandarin collar", "sub": "With a front slit", "layer": L["k_mand"], "kind": "own",
                      "joins": neck_joins, "source": "the owner's mandarin edit of the kurta photo"},
                     {"id": "boat", "name": "Boat neck", "sub": "Wide and shallow", "layer": L["k_boat"], "kind": "own",
                      "joins": neck_joins, "source": "the owner's boat-neck edit of the kurta photo"}]}}},
        ],
    }


def compose(look, picks):
    """The look's base with the chosen option of each slot, in slot order (z): what the page shows."""
    im = Image.open(os.path.join(DEMO, look["base"]["file"])).convert("RGBA")
    for o in picks:
        if o and o.get("layer"):
            lay = Image.open(os.path.join(DEMO, o["layer"]["file"])).convert("RGBA")
            im.alpha_composite(lay, tuple(o["layer"]["box"][:2]))
    return im.convert("RGB")


# the thumbnail crop of each slot, in frame px (x0, y0, x1, y1): the upper body for sleeves, the neck for necklines
THUMB_BOX = {"lehenga": {"sleeve": (200, 140, 1000, 940), "neck": (450, 120, 750, 420), "look": (100, 0, 1100, 1333)},
             "anarkali": {"sleeve": (250, 160, 950, 860), "neck": (470, 130, 730, 390), "look": (150, 0, 1050, 1200)},
             "straight-kurta": {"sleeve": (200, 200, 1000, 1000), "neck": (450, 180, 750, 480), "look": (150, 0, 1050, 1200)}}


def thumbs(manifest):
    """A small picture per option (its slot, with the other slot at its default), and one per look: the picker's cards."""
    for look in manifest["looks"]:
        sl = look["slots"]
        default = {k: next(o for o in v["options"] if o["id"] == v["default"]) for k, v in sl.items()}
        boxes = THUMB_BOX[look["id"]]
        im = compose(look, [default["sleeve"], default["neck"]])
        rel = f"assets/layers/{look['id']}/thumb-look.jpg"
        im.crop(boxes["look"]).resize((180, 240), Image.LANCZOS).save(os.path.join(DEMO, rel), quality=86)
        look["thumb"] = rel
        for slot, spec in sl.items():
            for o in spec["options"]:
                if o["kind"] == "missing":
                    continue
                picks = [o if s == slot else default[s] for s in ("sleeve", "neck")]
                im = compose(look, picks)
                rel = f"assets/layers/{look['id']}/thumb-{slot}-{o['id']}.jpg"
                im.crop(boxes[slot]).resize((160, 160), Image.LANCZOS).save(os.path.join(DEMO, rel), quality=86)
                o["thumb"] = rel


def review_sheets(manifest):
    os.makedirs(REVIEW, exist_ok=True)
    for look in manifest["looks"]:
        base = Image.open(os.path.join(DEMO, look["base"]["file"])).convert("RGBA")
        sl, nk = look["slots"]["sleeve"]["options"], look["slots"]["neck"]["options"]
        sl = [o for o in sl if o["kind"] != "missing"]
        nk = [o for o in nk if o["kind"] != "missing"]
        tw, th = 300, 400
        sheet = Image.new("RGB", (tw * len(sl), th * len(nk)), "white")
        for j, n in enumerate(nk):
            for i, s in enumerate(sl):
                im = base.copy()
                for o in (s, n):
                    if o["layer"]:
                        lay = Image.open(os.path.join(DEMO, o["layer"]["file"])).convert("RGBA")
                        x, y = o["layer"]["box"][:2]
                        im.alpha_composite(lay, (x, y))
                im = im.convert("RGB")
                im.save(os.path.join(REVIEW, f"{look['id']}--{s['id']}--{n['id']}.jpg"), quality=88)
                sheet.paste(im.resize((tw, th), Image.LANCZOS), (i * tw, j * th))
        sheet.save(os.path.join(REVIEW, f"{look['id']}-sheet.jpg"), quality=88)


if __name__ == "__main__":
    build(review="--review" in sys.argv)
