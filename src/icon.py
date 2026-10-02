"""Icône de Carnet : un anneau en trois arcs aux couleurs des macros (protéines, glucides, lipides), ouvert en bas."""
import math
P, C, F = '#72a2da', '#e29d52', '#52b48d'
BG_TOP, BG_BOTTOM = '#1a201b', '#0c0f0d'

def arc(cx, cy, r, a0, a1):
    x0, y0 = cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))
    x1, y1 = cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1))
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return f'M{x0:.2f} {y0:.2f}A{r} {r} 0 {large} 1 {x1:.2f} {y1:.2f}'

def glyph(cx=256, cy=256, r=146, sw=54, gap=13):
    cap = math.degrees((sw / 2) / r)
    span = 120 - gap - 2 * cap
    out = []
    for i, col in enumerate((P, C, F)):
        mid = -90 + 120 * i
        out.append(f'<path d="{arc(cx, cy, r, mid - span / 2, mid + span / 2)}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="round"/>')
    return ''.join(out)

def icon_svg(rounded=True, scale=1.0, plus=False):
    rx = 115 if rounded else 0
    bg = (f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG_BOTTOM}"/></linearGradient></defs>'
          f'<rect width="512" height="512" rx="{rx}" fill="url(#g)"/>')
    g = glyph()
    if plus:
        g = '<path d="M256 150v212M150 256h212" stroke="#e8ebe7" stroke-width="44" stroke-linecap="round" fill="none"/>'
    if scale != 1.0:
        g = f'<g transform="translate(256 256) scale({scale}) translate(-256 -256)">{g}</g>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">{bg}{g}</svg>'

def glyph_svg():
    """L’anneau seul, sur fond transparent (écran de lancement)."""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="66 66 380 380">{glyph()}</svg>'
