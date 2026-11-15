#!/usr/bin/env python3
"""Bake ASCII sphere rotations; Plasma only moves small textures at runtime."""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

TAU = math.tau
FRAMES = 48
GLYPHS = '.,:;=+ox%#@'
COLORS = ['#ffc76b', '#b8b2aa', '#edc995', '#6bbde5', '#e38d72',
          '#dfb38a', '#e4c998', '#8bd5d2', '#789fe9']
RADII = [73, 11, 18, 23, 16, 47, 36, 27, 25]
FONT = ImageFont.truetype('/usr/share/fonts/TTF/DejaVuSansMono.ttf', 10)
TARGET = Path(__file__).resolve().parents[1] / 'contents/ui/sprites'


def hash_value(n):
    return (math.sin(n * 127.1 + 311.7) * 43758.5453) % 1


def render(kind, radius, tint, frame):
    extent = radius * (2.05 if kind == 5 else 1.6 if kind == -1 else 1.15)
    size = math.ceil(extent * 2)
    image = Image.new('RGBA', (size, size))
    draw = ImageDraw.Draw(image)
    rgb = tuple(int(tint[i:i+2], 16) / 255 for i in (1, 3, 5))
    phase = frame / FRAMES * TAU

    def ink(x, y, glyph, strength, color=rgb):
        fill = tuple(max(0, min(255, round(c * strength * 255))) for c in color) + (255,)
        draw.text((size / 2 + x, size / 2 + y), glyph, font=FONT, fill=fill, anchor='mm')

    def rings(front):
        for band in range(3):
            outer = radius * (1.48 + band * 0.19)
            for step in range(58):
                a = step / 58 * TAU
                x, y = math.cos(a) * outer, math.sin(a) * outer * 0.30
                if (math.sin(a) > 0) == front:
                    ink(x * 0.94 + y * 0.34, -x * 0.34 + y * 0.94,
                        '=' if band == 1 else ':', 0.77 if front else 0.43)

    if kind == 5:
        rings(False)
    if kind == -1:
        for n in range(130):
            angle = n * 2.39996
            corona = radius * (1.08 + 0.29 * hash_value(n) + 0.03 * math.sin(phase + n))
            ink(math.cos(angle) * corona, math.sin(angle) * corona,
                '+' if n % 3 == 0 else '.', 0.18 + hash_value(n + 4) * 0.30)
    for py in range(-radius, radius + 1, 9):
        for px in range(-radius, radius + 1, 6):
            nx, ny = px / radius, py / radius
            if nx * nx + ny * ny > 1:
                continue
            nz = math.sqrt(1 - nx * nx - ny * ny)
            lon, lat = math.atan2(nx, nz) + phase, math.asin(ny)
            texture = 0.5 + 0.23 * math.sin(lon * 7 + lat * 9) + 0.16 * math.sin(lon * 13 - lat * 17)
            if kind in (4, 5):
                texture = 0.52 + 0.22 * math.sin(ny * 23 + math.sin(lon * 4) * 0.9) + 0.12 * math.sin(ny * 57 + lon * 2)
            if kind == -1:
                texture = 0.60 + 0.24 * math.sin(nx * 11 + phase + math.sin(ny * 12 - phase)) * math.cos(ny * 13 + phase)
            light = 0.82 + nz * 0.24 if kind == -1 else 0.28 + max(0, nx * -0.43 + ny * -0.23 + nz * 0.78) * 0.85
            value = max(0, min(1, texture * 0.66 + light * 0.34))
            glyph = GLYPHS[min(len(GLYPHS) - 1, int(value * len(GLYPHS)))]
            if kind == 2:
                land = math.sin(lon * 4 + math.sin(lat * 6)) + math.cos(lon * 6 - lat * 4.5) * 0.55
                color = (0.75, 0.89, 0.95) if abs(ny) > 0.83 or texture > 0.83 else (0.41, 0.76, 0.52) if land > 0.28 else (0.26, 0.59, 0.89)
                ink(px, py, glyph, light, color)
            else:
                ink(px, py, glyph, light * (0.67 + texture * 0.42))
    if kind == 5:
        rings(True)
    return image


if __name__ == '__main__':
    TARGET.mkdir(parents=True, exist_ok=True)
    for index, (radius, color) in enumerate(zip(RADII, COLORS)):
        frames = [render(index - 1, radius, color, f) for f in range(FRAMES)]
        size = frames[0].width
        sheet = Image.new('RGBA', (size * 8, size * 6))
        for f, image in enumerate(frames):
            sheet.paste(image, (f % 8 * size, f // 8 * size))
        target = TARGET / f'{index - 1}.png'
        sheet.save(target, optimize=True)
        print(target.name, sheet.size, target.stat().st_size)
