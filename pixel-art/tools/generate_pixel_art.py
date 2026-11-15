#!/usr/bin/env python3
"""Pre-render the pixel-art sprites for the solar-system wallpaper.

Every planet is ray-cast once per rotation step and per sun direction, so Plasma
only moves and clips small textures at runtime. Needs numpy and Pillow.

    python3 tools/generate_pixel_art.py [--sheet preview.png]
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'contents/ui/art'
ATLAS_JS = ROOT / 'contents/ui/Atlas.js'

TAU = math.tau
ROT = 64           # rotation frames per planet
LIGHT = 32         # sun directions, one per orbital-angle step
SUN_FRAMES = 96
SHIP_DIRS = 16
SQUASH = 0.44      # must match Geometry.js
TILT = -0.12       # must match Geometry.js
DEPTH = math.sqrt(1 - SQUASH ** 2)


# ---------------------------------------------------------------- helpers

def bayer(n):
    m = np.array([[0]])
    while m.shape[0] < n:
        m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
    return (m + 0.5) / m.size


B4, B8 = bayer(4), bayer(8)


def dither(h, w, m=B4):
    k = m.shape[0]
    return np.tile(m, (h // k + 1, w // k + 1))[:h, :w]


def rgb(h):
    h = h.lstrip('#')
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def ramp(*colors):
    return [rgb(c) for c in colors]


def _hash(ix, iy, iz, seed):
    h = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed * 2654435761)
    h &= 0xffffffff
    h = ((h ^ (h >> 15)) * 0x2c1b3c6d) & 0xffffffff
    h = ((h ^ (h >> 12)) * 0x297a2d39) & 0xffffffff
    h ^= h >> 15
    return (h & 0xffffff) / float(0xffffff)


def noise(x, y, z, seed=0):
    x, y, z = (np.asarray(a, dtype=np.float64) for a in (x, y, z))
    x, y, z = np.broadcast_arrays(x, y, z)
    fx, fy, fz = np.floor(x), np.floor(y), np.floor(z)
    u, v, w = x - fx, y - fy, z - fz
    u, v, w = (t * t * (3 - 2 * t) for t in (u, v, w))
    ix, iy, iz = fx.astype(np.int64), fy.astype(np.int64), fz.astype(np.int64)

    def c(dx, dy, dz):
        return _hash(ix + dx, iy + dy, iz + dz, seed)

    x00 = c(0, 0, 0) + u * (c(1, 0, 0) - c(0, 0, 0))
    x10 = c(0, 1, 0) + u * (c(1, 1, 0) - c(0, 1, 0))
    x01 = c(0, 0, 1) + u * (c(1, 0, 1) - c(0, 0, 1))
    x11 = c(0, 1, 1) + u * (c(1, 1, 1) - c(0, 1, 1))
    y0 = x00 + v * (x10 - x00)
    y1 = x01 + v * (x11 - x01)
    return y0 + w * (y1 - y0)


def fbm(x, y, z, octaves=4, seed=0, gain=0.5):
    total, amp, norm, f = 0.0, 1.0, 0.0, 1.0
    for o in range(octaves):
        total = total + amp * noise(x * f, y * f, z * f, seed + o * 101)
        norm += amp
        amp *= gain
        f *= 2.03
    return total / norm


_SPHERE = np.random.default_rng(7).normal(size=(3, 30000))
_SPHERE /= np.linalg.norm(_SPHERE, axis=0)


def quantile(fn, *qs):
    """Threshold values so a texture covers a predictable share of a sphere."""
    values = fn(*_SPHERE)
    return [float(v) for v in np.quantile(values, qs)]


def latitude(y):
    return np.arcsin(np.clip(-y, -1, 1))


def longitude(x, z):
    return np.arctan2(x, z)


def wrap(a):
    return (a + math.pi) % TAU - math.pi


# ---------------------------------------------------------------- geometry

def view_to_body(nx, ny, nz, alpha, beta, phi):
    """View space (x right, y down, z to viewer) -> spinning body space (y = pole)."""
    cb, sb = math.cos(-beta), math.sin(-beta)
    x1, y1 = nx * cb - ny * sb, nx * sb + ny * cb
    ca, sa = math.cos(-alpha), math.sin(-alpha)
    y2, z2 = y1 * ca - nz * sa, y1 * sa + nz * ca
    cp, sp = math.cos(phi), math.sin(phi)
    return x1 * cp + z2 * sp, y2, -x1 * sp + z2 * cp


def pole(alpha, beta):
    return np.array([-math.cos(alpha) * math.sin(beta), math.cos(alpha) * math.cos(beta), math.sin(alpha)])


def light_dir(j):
    """Direction from a planet at orbital step j towards the Sun, in view space."""
    th = TAU * j / LIGHT
    # Depth is softened on purpose: planets in front of the Sun read as wide crescents.
    lx, ly, lz = -math.cos(th), -SQUASH * math.sin(th), -DEPTH * math.sin(th) * 0.55
    ct, st = math.cos(TILT), math.sin(TILT)
    v = np.array([lx * ct - ly * st, lx * st + ly * ct, lz])
    return v / np.linalg.norm(v)


def shade(b, dith, thresholds=(-0.07, 0.16, 0.5, 0.86), spread=0.16):
    v = b[..., None] + (dith[..., None] - 0.5) * spread
    return (v > np.array(thresholds)).sum(-1)


# ---------------------------------------------------------------- planets

def mercury_tex(at):
    x, y, z = at(1)
    dark = fbm(x * 2.6, y * 2.6, z * 2.6, 4, 3) > MERC[0]
    pale = fbm(x * 5 + 9, y * 5, z * 5, 3, 4) > MERC[1]
    return np.where(pale, 2, np.where(dark, 1, 0)), {}


def venus_tex(at):
    x, y, z = at(1)
    lat = latitude(y)
    warp = fbm(x * 2, y * 2, z * 2, 3, 13)
    s = fbm(x * 1.3 + warp, (lat * 3.2 + np.abs(lat) * 2.2 + warp * 1.6), z * 1.3, 4, 14)
    return np.digitize(s, VENUS), {}


def earth_tex(at):
    x, y, z = at(1)
    lat = latitude(y)
    h = fbm(x * 1.7 + 3, y * 1.7, z * 1.7, 5, 11)
    land = h > EARTH['land']
    shallow = (h > EARTH['shallow']) & ~land
    dry = (fbm(x * 3, y * 3, z * 3, 3, 5) + (0.32 - np.abs(np.abs(lat) - 0.4)) * 0.5) > EARTH['dry']
    ice = np.abs(lat) > 1.16 + 0.22 * (fbm(x * 4, y * 4, z * 4, 2, 6) - 0.5)
    cx, cy, cz = at(2)
    clat = latitude(cy)
    c = fbm(cx * 2.3 + 1, cy * 4.6 + clat, cz * 2.3, 4, 7)
    cloud = c > EARTH['cloud']
    lights = land & ~ice & (fbm(x * 9, y * 9, z * 9, 2, 21) > EARTH['lights'])
    mat = np.where(shallow, 1, 0)
    mat = np.where(land, np.where(dry, 3, 2), mat)
    mat = np.where(ice, 4, mat)
    mat = np.where(cloud, 5, mat)
    return mat, {'lights': lights & ~cloud, 'ocean': ~land & ~ice & ~cloud}


def earth_post(c):
    night = c.level == 0
    lights = c.extra['lights'] & night
    c.col[lights] = np.where((c.dith[lights] > 0.45)[:, None], rgb('#ffd56e'), rgb('#ff9b40'))
    rz = 2 * c.b * c.nz - c.light[2]
    glint = c.extra['ocean'] & (rz > 0.94) & (c.level >= 3)
    c.col[glint] = rgb('#d4f1ff')


def moon_tex(at):
    x, y, z = at(1)
    return np.where(fbm(x * 2.2, y * 2.2, z * 2.2, 3, 41) > MOON[0], 1, 0), {}


def mars_tex(at):
    x, y, z = at(1)
    lat = latitude(y)
    dark = fbm(x * 2.2, y * 2.2, z * 2.2, 4, 51) > MARS[0]
    dust = fbm(x * 3.5 + 5, y * 3.5, z * 3.5, 3, 52) > MARS[1]
    ice = np.abs(lat) > 1.2 + 0.2 * (fbm(x * 5, y * 5, z * 5, 2, 53) - 0.5)
    mat = np.where(dark, 1, np.where(dust, 2, 0))
    return np.where(ice, 3, mat), {}


def band_tex(at, table, turbulence, seed, fast=()):
    x, y, z = at(1)
    lat = latitude(y)
    fx, fy, fz = at(2)
    wobble = fbm(x * 3, y * 3, z * 3, 4, seed) - 0.5
    quick = fbm(fx * 3.4, fy * 7, fz * 3.4, 4, seed + 1) - 0.5
    in_fast = np.zeros_like(lat, dtype=bool)
    for lo, hi in fast:
        in_fast |= (lat > lo) & (lat < hi)
    l = lat + np.where(in_fast, quick, wobble) * turbulence
    edges = np.array([e for e, _ in table[1:]])
    mats = np.array([m for _, m in table])
    return mats[np.digitize(l, edges)], lat, (x, y, z), (fx, fy, fz)


JUPITER_BANDS = [(-9, 4), (-1.05, 1), (-0.66, 0), (-0.45, 2), (-0.26, 0), (-0.1, 5),
                 (0.1, 2), (0.3, 0), (0.48, 1), (0.66, 0), (1.0, 4)]


def jupiter_tex(at):
    mat, lat, (x, y, z), (fx, fy, fz) = band_tex(at, JUPITER_BANDS, 0.16, 31, fast=((-0.12, 0.12),))
    lon = longitude(x, z)
    spot = ((wrap(lon - 0.6) / 0.42) ** 2 + ((lat + 0.36) / 0.12) ** 2)
    mat = np.where(spot < 1.7, 0, mat)
    mat = np.where(spot < 1.0, 3, mat)
    ovals = ((wrap(lon + 2.2) / 0.16) ** 2 + ((lat + 0.62) / 0.06) ** 2 < 1) | \
            ((wrap(lon - 2.6) / 0.14) ** 2 + ((lat - 0.55) / 0.05) ** 2 < 1)
    mat = np.where(ovals, 5, mat)
    festoon = (np.abs(lat) < 0.12) & (fbm(fx * 6, fy * 6, fz * 6, 2, 35) > JUP[0])
    return np.where(festoon, 2, mat), {}


SATURN_BANDS = [(-9, 3), (-0.95, 1), (-0.55, 0), (-0.3, 2), (0.3, 0), (0.55, 1), (0.95, 3)]


def saturn_tex(at):
    mat, lat, _, _ = band_tex(at, SATURN_BANDS, 0.1, 61)
    return mat, {}


def uranus_tex(at):
    x, y, z = at(1)
    lat = latitude(y)
    mat = np.where(lat > 0.85 + 0.1 * (fbm(x * 4, y * 4, z * 4, 2, 71) - 0.5), 1, 0)
    mat = np.where((np.abs(lat + 0.35) < 0.07), 2, mat)
    return mat, {}


def neptune_tex(at):
    x, y, z = at(1)
    lat = latitude(y)
    lon = longitude(x, z)
    wob = fbm(x * 3, y * 3, z * 3, 3, 81) - 0.5
    mat = np.where(np.abs(lat + 0.42 + wob * 0.15) < 0.12, 1, 0)
    streak = fbm(x * 2, y * 9, z * 2, 3, 82) > NEP[0]
    mat = np.where(streak & (np.abs(np.abs(lat) - 0.55) < 0.22), 2, mat)
    spot = (wrap(lon - 1.1) / 0.36) ** 2 + ((lat + 0.36) / 0.13) ** 2
    mat = np.where(spot < 1, 3, mat)
    companion = (wrap(lon - 1.0) / 0.26) ** 2 + ((lat + 0.56) / 0.05) ** 2 < 1
    return np.where(companion, 2, mat), {}


def saturn_ring(rho):
    density = np.zeros_like(rho)
    density = np.where((rho > 1.24) & (rho < 1.52), 0.4, density)
    density = np.where((rho >= 1.52) & (rho < 1.94), 1.0, density)
    density = np.where((rho >= 2.03) & (rho < 2.28), 0.9, density)
    band = np.where(rho < 1.52, 0, np.where(rho < 1.73, 1, np.where(rho < 1.94, 2, 3)))
    return density, band


def uranus_ring(rho):
    density = np.where((rho > 1.62) & (rho < 1.82), 0.55, 0.0)
    return density, np.zeros(rho.shape, dtype=int)


# Thresholds derived from the noise distribution (share of the sphere covered).
MERC = quantile(lambda x, y, z: fbm(x * 2.6, y * 2.6, z * 2.6, 4, 3), 0.62) + \
       quantile(lambda x, y, z: fbm(x * 5 + 9, y * 5, z * 5, 3, 4), 0.9)
VENUS = quantile(lambda x, y, z: fbm(x * 1.3, latitude(y) * 5, z * 1.3, 4, 14), 0.3, 0.75)
_EH = lambda x, y, z: fbm(x * 1.7 + 3, y * 1.7, z * 1.7, 5, 11)
EARTH = dict(zip(['shallow', 'land'], quantile(_EH, 0.52, 0.64)))
EARTH['dry'] = quantile(lambda x, y, z: fbm(x * 3, y * 3, z * 3, 3, 5), 0.66)[0]
EARTH['cloud'] = quantile(lambda x, y, z: fbm(x * 2.3 + 1, y * 4.6 + latitude(y), z * 2.3, 4, 7), 0.7)[0]
EARTH['lights'] = quantile(lambda x, y, z: fbm(x * 9, y * 9, z * 9, 2, 21), 0.55)[0]
MOON = quantile(lambda x, y, z: fbm(x * 2.2, y * 2.2, z * 2.2, 3, 41), 0.68)
MARS = quantile(lambda x, y, z: fbm(x * 2.2, y * 2.2, z * 2.2, 4, 51), 0.7) + \
       quantile(lambda x, y, z: fbm(x * 3.5 + 5, y * 3.5, z * 3.5, 3, 52), 0.82)
JUP = quantile(lambda x, y, z: fbm(x * 6, y * 6, z * 6, 2, 35), 0.8)
NEP = quantile(lambda x, y, z: fbm(x * 2, y * 9, z * 2, 3, 82), 0.86)

NIGHT = '#070a18'
BODIES = [
    dict(key='mercurio', name='MERCURIO', radius=3, alpha=-0.1, beta=0.0, spin=1, texture=mercury_tex,
         label='#a39a92', ramps=[ramp(NIGHT, '#3d3631', '#6e645c', '#9c9087', '#c9bdb1'),
                                 ramp(NIGHT, '#2b2622', '#4b4440', '#6c635c', '#8a8078'),
                                 ramp(NIGHT, '#4a433e', '#8a7f75', '#b9ad9f', '#e2d6c6')]),
    dict(key='venus', name='VENUS', radius=5, alpha=-0.1, beta=0.05, spin=-1, texture=venus_tex,
         label='#d9b77e', rim='#ffe9b8',
         ramps=[ramp(NIGHT, '#5c4322', '#9a7440', '#c9a062', '#e8c890'),
                ramp(NIGHT, '#6a4e2a', '#b08850', '#dcb878', '#f4dca4'),
                ramp(NIGHT, '#7a5e36', '#c49a5c', '#ecc98a', '#fff0c4')]),
    dict(key='tierra', name='TIERRA', radius=7, alpha=-0.38, beta=-0.42, spin=1, texture=earth_tex,
         post=earth_post, label='#7cc4e8', rim='#7fd8ff',
         ramps=[ramp('#060b1e', '#122458', '#1c468a', '#2866b4', '#3a86d0'),
                ramp('#081028', '#173c76', '#2468a6', '#3790c8', '#56b2de'),
                ramp('#081410', '#1d4630', '#2e7438', '#4c9e40', '#7ac052'),
                ramp('#120f10', '#55422a', '#8c6a3a', '#bc9852', '#d8be78'),
                ramp('#141a2c', '#5a6e8c', '#a8bcd4', '#e2ecf6', '#ffffff'),
                ramp('#121828', '#66748e', '#b4c0d2', '#ebf0f7', '#ffffff')]),
    dict(key='marte', name='MARTE', radius=5, alpha=-0.3, beta=-0.38, spin=1, texture=mars_tex,
         label='#e0896a', rim='#ffb08a',
         ramps=[ramp(NIGHT, '#5a2418', '#9a3e22', '#c8603a', '#e08a5a'),
                ramp(NIGHT, '#3e1a14', '#6a2c1e', '#8e4428', '#a85a36'),
                ramp(NIGHT, '#6e3a22', '#b0623a', '#d88a56', '#f0b07a'),
                ramp('#141a2c', '#7a8090', '#c4c8d4', '#eef0f6', '#ffffff')]),
    dict(key='jupiter', name='JUPITER', radius=16, alpha=-0.12, beta=-0.06, spin=1, texture=jupiter_tex,
         label='#dcb48c',
         ramps=[ramp(NIGHT, '#6a5a48', '#bca888', '#e4d4b4', '#f8ecd4'),
                ramp(NIGHT, '#5a3e2c', '#9a6a48', '#c89466', '#e0b48a'),
                ramp(NIGHT, '#4a2a1e', '#7a4630', '#a26244', '#bc7e5a'),
                ramp(NIGHT, '#6a2418', '#a8402a', '#d0603e', '#e8845a'),
                ramp(NIGHT, '#4c3c34', '#7e6a5a', '#a8907a', '#c4ac94'),
                ramp(NIGHT, '#7a7470', '#c8c0b8', '#f0ece4', '#ffffff')]),
    dict(key='saturno', name='SATURNO', radius=13, alpha=-0.44, beta=-0.34, spin=1, texture=saturn_tex,
         label='#e4cb92', ring=dict(outer=2.3, shape=saturn_ring,
                                    ramps=[ramp('#0c0c10', '#2e2c2c', '#4c4844', '#6a645c', '#857d72'),
                                           ramp('#100e0c', '#6a5c44', '#a8946c', '#d4c094', '#ecdcb4'),
                                           ramp('#100e0c', '#7a6c50', '#c0ac82', '#e6d6aa', '#fbf0cc'),
                                           ramp('#0e0c0a', '#5a4e3c', '#8e7c5e', '#b4a07c', '#cebc98')]),
         ramps=[ramp(NIGHT, '#6a5a38', '#b49c64', '#dcc488', '#f2e0aa'),
                ramp(NIGHT, '#5a4a2e', '#947c50', '#bca06c', '#d4ba86'),
                ramp(NIGHT, '#7a6e4c', '#c8b888', '#ece0b0', '#fff6d4'),
                ramp(NIGHT, '#3e4852', '#687a84', '#90a2a8', '#b4c4c4')]),
    dict(key='urano', name='URANO', radius=9, alpha=-0.72, beta=1.36, spin=-1, texture=uranus_tex,
         label='#8ed6d4', rim='#c4fffb', ring=dict(outer=1.85, shape=uranus_ring,
                                                    ramps=[ramp('#0a0e12', '#24343c', '#3c5660', '#587a82', '#7a9ea4')]),
         ramps=[ramp('#060f14', '#2a5a62', '#4e9aa2', '#7ccacc', '#a8e6e2'),
                ramp('#081216', '#346a70', '#62b0b4', '#94dcd8', '#c4f2ee'),
                ramp('#050d12', '#24525a', '#468e96', '#70bcbe', '#98d8d6')]),
    dict(key='neptuno', name='NEPTUNO', radius=9, alpha=-0.3, beta=-0.42, spin=1, texture=neptune_tex,
         label='#7fa2ea', rim='#9cc0ff',
         ramps=[ramp('#050818', '#1a2a6a', '#2a4aa8', '#3e6ad4', '#6a94ec'),
                ramp('#040716', '#142058', '#203a8c', '#2e52b0', '#4a72cc'),
                ramp('#0c1024', '#5a6a90', '#a8b8dc', '#dce6fa', '#ffffff'),
                ramp('#03050f', '#0e1648', '#182a70', '#22388a', '#3048a0')]),
    dict(key='luna', name='LUNA', radius=2, alpha=0.0, beta=0.0, spin=1, rot=1, texture=moon_tex,
         label='#a4a4ac', ramps=[ramp(NIGHT, '#3a3a40', '#6e6e74', '#a4a4a8', '#d4d4d6'),
                                 ramp(NIGHT, '#2a2a30', '#4a4a52', '#6e6e76', '#8e8e96')]),
]


class Ctx:
    pass


def render_body(spec):
    r = spec['radius']
    alpha, beta = spec['alpha'], spec['beta']
    n = pole(alpha, beta)
    ring = spec.get('ring')
    hw = hh = r + 1
    if ring:
        ro = ring['outer'] * r
        hw = max(hw, ro * math.sqrt(max(0.0, 1 - n[0] ** 2)) + 1)
        hh = max(hh, ro * math.sqrt(max(0.0, 1 - n[1] ** 2)) + 1)
    w, h = 2 * math.ceil(hw), 2 * math.ceil(hh)
    ys, xs = np.mgrid[0:h, 0:w]
    X, Y = xs + 0.5 - w / 2, ys + 0.5 - h / 2
    d2 = X * X + Y * Y
    sphere = d2 <= r * r + r * 0.4
    Zs = np.sqrt(np.clip(r * r - d2, 0, None))
    length = np.sqrt(d2 + Zs * Zs)
    length[length == 0] = 1
    NX, NY, NZ = X / length, Y / length, Zs / length
    edge = sphere & (d2 > (r - 1.05) ** 2)
    dith = dither(h, w)
    rots = spec.get('rot', ROT)
    palette = np.array(spec['ramps'], dtype=np.float64)
    # Night side: a deep tint of each material so the dark limb stays readable.
    palette[:, 0] = palette[:, 1] * 0.3 + np.array(rgb('#080a1c')) * 0.7
    palette = palette.round().astype(np.uint8)

    textures = []
    for f in range(rots):
        phi = -spec['spin'] * TAU * f / rots

        def at(k, phi=phi):
            return view_to_body(NX, NY, NZ, alpha, beta, k * phi)
        textures.append(spec['texture'](at))

    if ring:
        Zr = -(n[0] * X + n[1] * Y) / n[2]
        rho = np.sqrt(d2 + Zr * Zr) / r
        density, band = ring['shape'](rho)
        ring_vis = (density > dith) & (~sphere | (Zr > Zs))
        ring_pal = np.array(ring['ramps'], dtype=np.uint8)

    atlas = np.zeros((h * LIGHT, w * rots, 4), np.uint8)
    for j in range(LIGHT):
        L = light_dir(j)
        b = NX * L[0] + NY * L[1] + NZ * L[2]
        level = shade(b, dith)
        if ring:
            P = np.stack([X, Y, Zs])
            nl = float(n @ L)
            if abs(nl) > 1e-4:
                t = -(np.tensordot(n, P, 1)) / nl
                Q = P + t * L[:, None, None]
                qd, _ = ring['shape'](np.linalg.norm(Q, axis=0) / r)
                shadow = sphere & (t > 0) & (qd > 0.5)
                level = np.where(shadow, np.minimum(level, np.maximum(level - 2, 1)), level)
            R = np.stack([X, Y, Zr])
            rl = np.tensordot(L, R, 1)
            disc = rl * rl - (np.sum(R * R, axis=0) - r * r)
            in_shadow = (disc > 0) & (-rl - np.sqrt(np.clip(disc, 0, None)) > 0)
            lit = nl * n[2] > 0
            ring_level = np.full(level.shape, 3 if lit else 2)
            ring_level = np.where(dith > 0.82, ring_level + 1, ring_level)
            ring_level = np.where(in_shadow, 1, ring_level)
            ring_rgb = ring_pal[band, np.clip(ring_level, 0, 4)]
        for f in range(rots):
            mat, extra = textures[f]
            col = palette[mat, level].copy()
            if 'post' in spec:
                c = Ctx()
                c.col, c.level, c.b, c.nz, c.light, c.extra, c.dith = col, level, b, NZ, L, extra, dith
                spec['post'](c)
            if 'rim' in spec:
                col[edge & (b > -0.02)] = rgb(spec['rim'])
            frame = np.zeros((h, w, 4), np.uint8)
            frame[sphere, :3] = col[sphere]
            frame[sphere, 3] = 255
            if ring:
                frame[ring_vis, :3] = ring_rgb[ring_vis]
                frame[ring_vis, 3] = 255
            atlas[j * h:(j + 1) * h, f * w:(f + 1) * w] = frame
    Image.fromarray(atlas, 'RGBA').save(OUT / f"{spec['key']}.png", optimize=True)
    return {'src': f"art/{spec['key']}.png", 'w': w, 'h': h, 'cols': rots, 'rows': LIGHT, 'radius': r}


# ---------------------------------------------------------------- the Sun

SUN_RADIUS = 28
SUN_RAMP = ['#fffef2', '#fff3b0', '#ffd862', '#ffb02e', '#f5801c', '#d4521a', '#8e2a14']
CORONA = ['#ffc54c', '#ff922c', '#e2581c', '#a0301a', '#5a1a16']


def looped(fn, t, offset):
    """Seamless loop: blend the field at t and t-1 so frame 0 follows the last one."""
    return fn(t * offset) * (1 - t) + fn((t - 1) * offset) * t


def render_sun():
    R = SUN_RADIUS
    half = math.ceil(R * 1.85)
    size = 2 * half
    ys, xs = np.mgrid[0:size, 0:size]
    X, Y = xs + 0.5 - half, ys + 0.5 - half
    d = np.sqrt(X * X + Y * Y) / R
    disc = d * d <= 1 + 0.4 / R
    mu = np.sqrt(np.clip(1 - d * d, 0, 1))
    NX, NY, NZ = X / R, Y / R, mu
    angle = np.arctan2(Y, X)
    dith4, dith8 = dither(size, size), dither(size, size, B8)
    pal, cor = np.array([rgb(c) for c in SUN_RAMP]), np.array([rgb(c) for c in CORONA])
    cols = 12
    atlas = np.zeros((size * (SUN_FRAMES // cols), size * cols, 4), np.uint8)
    flares = [(0.6, 0.0), (2.5, 0.33), (4.3, 0.66)]   # (limb angle, start phase)
    for f in range(SUN_FRAMES):
        t = f / SUN_FRAMES
        bx, by, bz = view_to_body(NX, NY, NZ, -0.12, -0.1, -TAU * t)
        gran = looped(lambda o: fbm(bx * 6 + o, by * 6, bz * 6 + o * 0.5, 3, 91), t, 1.3)
        lat, lon = latitude(by), longitude(bx, bz)
        spots = np.zeros_like(d)
        for slon, slat, s in ((0.4, 0.3, 0.16), (2.4, -0.25, 0.12), (2.6, -0.3, 0.07), (4.6, 0.22, 0.1)):
            spots = np.maximum(spots, 1 - ((wrap(lon - slon) / s) ** 2 + ((lat - slat) / (s * 0.8)) ** 2))
        light = 0.5 + 0.38 * mu + (gran - 0.5) * 1.25
        idx = np.clip(((1.0 - light) * 7.2 + (dith4 - 0.5) * 0.9).astype(int), 0, 6)
        idx = np.where(spots > 0, np.maximum(idx, 5), idx)
        idx = np.where(spots > 0.55, 6, idx)
        frame = np.zeros((size, size, 4), np.uint8)
        frame[disc, :3] = pal[idx[disc]]
        frame[disc, 3] = 255

        rays = looped(lambda o: fbm(np.cos(angle) * 2.2 + o, np.sin(angle) * 2.2, o * 0.7, 3, 92), t, 1.6)
        fade = np.clip(1 - (d - 1) / 0.82, 0, 1)
        dens = fade ** 1.8 * (0.42 + (rays - 0.35) * 1.5)
        corona = ~disc & (d < 1.82) & (dens > dith8)
        band = np.clip(((d - 1) / 0.82 * 4.2 + (dith4 - 0.5) * 0.8).astype(int), 0, 4)
        frame[corona, :3] = cor[band[corona]]
        frame[corona, 3] = 255

        for limb, start in flares:
            s = (t - start) % 1.0
            if s > 0.55:
                continue
            rise = math.sin(math.pi * s / 0.55)
            for u in np.linspace(0, math.pi, 46):
                a = limb + 0.13 * math.cos(u)
                rad = R * (1 + 0.38 * rise * math.sin(u)) - 0.5
                px, py = int(half + math.cos(a) * rad), int(half + math.sin(a) * rad)
                if 0 <= px < size and 0 <= py < size:
                    hot = math.sin(u) > 0.55 and rise > 0.5
                    frame[py, px] = rgb('#ffd59a' if hot else '#ff6a32') + [255]
        r0, c0 = divmod(f, cols)
        atlas[r0 * size:(r0 + 1) * size, c0 * size:(c0 + 1) * size] = frame
    Image.fromarray(atlas, 'RGBA').save(OUT / 'sol.png', optimize=True)
    return {'src': 'art/sol.png', 'w': size, 'h': size, 'cols': cols, 'frames': SUN_FRAMES, 'radius': R}


def render_halo():
    size = 260
    ys, xs = np.mgrid[0:size, 0:size]
    d = np.sqrt((xs + 0.5 - size / 2) ** 2 + (ys + 0.5 - size / 2) ** 2)
    dith = dither(size, size, B8)
    img = np.zeros((size, size, 4), np.uint8)
    for radius, color, strength in ((118, '#24122a', 0.42), (92, '#371822', 0.5), (70, '#52221a', 0.58)):
        dens = np.clip(1 - d / radius, 0, 1) ** 1.4 * strength * 1.6
        on = dens > dith
        img[on] = rgb(color) + [255]
    Image.fromarray(img, 'RGBA').save(OUT / 'halo.png', optimize=True)
    return {'src': 'art/halo.png', 'w': size, 'h': size}


# ---------------------------------------------------------------- background

def render_nebula():
    W, H = 1100, 680
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float64)
    wx = fbm(xs / 260, ys / 260, 3.3, 3, 42) - 0.5
    wy = fbm(xs / 260 + 7, ys / 260, 5.1, 3, 43) - 0.5
    purple = fbm((xs + 260 * wx) / 190, (ys + 260 * wy) / 190, 1.7, 5, 44)
    teal = fbm((xs - 200 * wy) / 230 + 4, (ys + 200 * wx) / 230, 2.9, 5, 45)
    band_dist = np.abs((ys - (0.42 * xs + 40)) / math.hypot(1, 0.42))
    milky = np.exp(-(band_dist / 120) ** 2) * (0.55 + (fbm(xs / 60, ys / 60, 8.8, 4, 46) - 0.5) * 1.4)
    dith = dither(H, W, B8)
    img = np.zeros((H, W, 3), np.uint8)
    img[:] = rgb('#04050d')

    def paint(value, lo, hi, colors):
        v = np.clip((value - lo) / (hi - lo), 0, 1) * len(colors) + (dith - 0.5) * 0.9
        lvl = np.floor(v).astype(int)
        for i, c in enumerate(colors):
            img[lvl == i + 1] = rgb(c)
        img[lvl > len(colors)] = rgb(colors[-1])

    p_lo, p_hi = np.quantile(purple, [0.55, 0.985])
    t_lo, t_hi = np.quantile(teal, [0.68, 0.995])
    paint(milky, 0.25, 1.15, ['#070818', '#0a0b1f'])
    paint(teal, t_lo, t_hi, ['#061218', '#081a22', '#0b222c'])
    paint(purple, p_lo, p_hi, ['#0b0819', '#110b23', '#180e2e', '#211236'])

    rng = np.random.default_rng(4)
    dust = rng.random((H, W)) < 0.0035 + 0.012 * np.clip(milky, 0, 1)
    tone = rng.random((H, W))
    img[dust & (tone < 0.6)] = rgb('#1a2036')
    img[dust & (tone >= 0.6)] = rgb('#262f4c')
    galaxies = [(['..aba..', 'abccba.', '.abba..'], 140, 90), (['.ab.', 'abca', '.ba.'], 880, 520),
                (['..ab...', '.abcba.', '...ba..'], 980, 120)]
    shades = {'a': '#1e2238', 'b': '#3a3c5c', 'c': '#8a86a8'}
    for rows, gx, gy in galaxies:
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch in shades:
                    img[gy + dy, gx + dx] = rgb(shades[ch])
    Image.fromarray(img, 'RGB').save(OUT / 'nebula.png', optimize=True)
    return {'src': 'art/nebula.png', 'w': W, 'h': H}


def render_sparkle():
    S = 9
    c = S // 2
    steps = [
        {(0, 0): '#53608a'},
        {(0, 0): '#c8d6ff', 1: '#3e4a72'},
        {(0, 0): '#ffffff', 1: '#9db2ea', 2: '#3e4a72'},
        {(0, 0): '#ffffff', 1: '#c8d6ff', 2: '#7b8fcc', 3: '#3e4a72', 'diag': '#56649a'},
        {(0, 0): '#ffffff', 1: '#e2eaff', 2: '#9db2ea', 3: '#6474ac', 4: '#343e62', 'diag': '#7b8fcc'},
    ]
    atlas = np.zeros((S, S * len(steps), 4), np.uint8)
    for i, step in enumerate(steps):
        for key, color in step.items():
            if key == (0, 0):
                pts = [(0, 0)]
            elif key == 'diag':
                pts = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            else:
                pts = [(key, 0), (-key, 0), (0, key), (0, -key)]
            for dx, dy in pts:
                atlas[c + dy, i * S + c + dx] = rgb(color) + [255]
    Image.fromarray(atlas, 'RGBA').save(OUT / 'destello.png', optimize=True)
    return {'src': 'art/destello.png', 'w': S, 'h': S, 'frames': len(steps)}


# ---------------------------------------------------------------- labels

GLYPHS = {
    'A': ['.#.', '#.#', '###', '#.#', '#.#'], 'C': ['.##', '#..', '#..', '#..', '.##'],
    'E': ['###', '#..', '##.', '#..', '###'], 'I': ['###', '.#.', '.#.', '.#.', '###'],
    'J': ['..#', '..#', '..#', '#.#', '.#.'], 'L': ['#..', '#..', '#..', '#..', '###'],
    'M': ['#...#', '##.##', '#.#.#', '#...#', '#...#'], 'N': ['#..#', '##.#', '#.##', '#..#', '#..#'],
    'O': ['.#.', '#.#', '#.#', '#.#', '.#.'], 'P': ['##.', '#.#', '##.', '#..', '#..'],
    'R': ['##.', '#.#', '##.', '#.#', '#.#'], 'S': ['.##', '#..', '.#.', '..#', '##.'],
    'T': ['###', '.#.', '.#.', '.#.', '.#.'], 'U': ['#.#', '#.#', '#.#', '#.#', '###'],
    'V': ['#.#', '#.#', '#.#', '#.#', '.#.'],
}


def render_label(key, text, color):
    width = sum(len(GLYPHS[ch][0]) for ch in text) + (len(text) - 1) * 1 + 2
    ink = np.zeros((7, width), bool)
    x = 1
    for ch in text:
        g = GLYPHS[ch]
        for gy, row in enumerate(g):
            for gx, cell in enumerate(row):
                ink[1 + gy, x + gx] |= cell == '#'
        x += len(g[0]) + 1
    halo = np.zeros_like(ink)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            halo |= np.roll(np.roll(ink, dy, 0), dx, 1)
    img = np.zeros((7, width, 4), np.uint8)
    img[halo & ~ink] = rgb('#03040b') + [190]
    img[ink] = rgb(color) + [255]
    path = OUT / f'nombre-{key}.png'
    Image.fromarray(img, 'RGBA').save(path, optimize=True)
    return {'src': f'art/{path.name}', 'w': width, 'h': 7}


# ---------------------------------------------------------------- spaceship

SHIP = ['............',
        '...rr.......',
        '...rwwwwd...',
        '.ofgwwwbwwr.',
        '...rggggd...',
        '...rr.......',
        '............']
SHIP_COLORS = {'w': '#e8ecf4', 'g': '#98a2b8', 'd': '#5a647c', 'r': '#e8483c', 'b': '#4fc0ff',
               'f': '#ffe066', 'o': '#ff7a1c'}


def scale2x(a):
    h, w = a.shape[:2]
    p = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode='edge')
    B, D, E, F, H = p[0:h, 1:w + 1], p[1:h + 1, 0:w], p[1:h + 1, 1:w + 1], p[1:h + 1, 2:w + 2], p[2:h + 2, 1:w + 1]

    def eq(u, v):
        return np.all(u == v, axis=-1)
    out = np.zeros((2 * h, 2 * w, a.shape[2]), a.dtype)
    out[0::2, 0::2] = np.where((eq(D, B) & ~eq(B, F) & ~eq(D, H))[..., None], D, E)
    out[0::2, 1::2] = np.where((eq(B, F) & ~eq(B, D) & ~eq(F, H))[..., None], F, E)
    out[1::2, 0::2] = np.where((eq(D, H) & ~eq(D, B) & ~eq(H, F))[..., None], D, E)
    out[1::2, 1::2] = np.where((eq(H, F) & ~eq(D, H) & ~eq(B, F))[..., None], F, E)
    return out


def render_ship():
    S = 15
    atlas = np.zeros((S * 2, S * SHIP_DIRS, 4), np.uint8)
    for flame in range(2):
        rows = [list(r) for r in SHIP]
        if flame:
            rows[3][1] = 'f'
            rows[3][2] = 'o'
        base = np.zeros((S, S, 4), np.uint8)
        oy, ox = (S - len(rows)) // 2, (S - len(rows[0])) // 2
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch in SHIP_COLORS:
                    base[oy + y, ox + x] = rgb(SHIP_COLORS[ch]) + [255]
        big = scale2x(scale2x(scale2x(base)))
        for i in range(SHIP_DIRS):
            angle = 360 * i / SHIP_DIRS           # 0 = pointing right, counter-clockwise on screen
            rot = np.array(Image.fromarray(big, 'RGBA').rotate(angle, resample=Image.NEAREST))
            small = rot[4::8, 4::8]
            atlas[flame * S:(flame + 1) * S, i * S:(i + 1) * S] = small
    Image.fromarray(atlas, 'RGBA').save(OUT / 'nave.png', optimize=True)
    return {'src': 'art/nave.png', 'w': S, 'h': S, 'cols': SHIP_DIRS}


# ---------------------------------------------------------------- main

def contact_sheet(path):
    files = sorted(OUT.glob('*.png'))
    images = [Image.open(f).convert('RGBA') for f in files]
    previews = []
    for im in images:
        crop = im.crop((0, 0, min(im.width, 640), min(im.height, 320)))
        previews.append(crop.resize((crop.width * 2, crop.height * 2), Image.NEAREST))
    width = max(p.width for p in previews)
    sheet = Image.new('RGBA', (width, sum(p.height + 8 for p in previews)), (20, 20, 30, 255))
    y = 0
    for p in previews:
        sheet.alpha_composite(p, (0, y))
        y += p.height + 8
    sheet.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sheet', type=Path, help='save a contact sheet of every sprite')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {'rotFrames': ROT, 'lightFrames': LIGHT, 'bodies': {}, 'labels': {}}
    for spec in BODIES:
        meta['bodies'][spec['key']] = render_body(spec)
        meta['labels'][spec['key']] = render_label(spec['key'], spec['name'], spec['label'])
        print('  ' + spec['key'])
    meta['labels']['sol'] = render_label('sol', 'SOL', '#f0b45a')
    meta['sun'] = render_sun()
    meta['halo'] = render_halo()
    meta['nebula'] = render_nebula()
    meta['sparkle'] = render_sparkle()
    meta['ship'] = render_ship()
    ATLAS_JS.write_text('.pragma library\n// Generado por tools/generate_pixel_art.py: no editar a mano.\n'
                        'var data = ' + json.dumps(meta, indent=1) + ';\n')
    print('Sprites en ' + str(OUT))
    if args.sheet:
        contact_sheet(args.sheet)
        print('Hoja de contacto: ' + str(args.sheet))


if __name__ == '__main__':
    main()
