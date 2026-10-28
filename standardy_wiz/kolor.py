"""Kolorymetria bez zależności: kontrast WCAG, CIELAB, CIEDE2000, symulacja zaburzeń widzenia barw
(Machado, Oliveira, Fernandes 2009, nasilenie 1,0)."""
from __future__ import annotations

import math
import re

_HEX = re.compile(r"^#?([0-9a-fA-F]{6})(?:[0-9a-fA-F]{2})?$")

# sRGB (D65) -> XYZ
_M_XYZ = ((0.4124564, 0.3575761, 0.1804375),
          (0.2126729, 0.7151522, 0.0721750),
          (0.0193339, 0.1191920, 0.9503041))
_BIEL = (0.95047, 1.0, 1.08883)

# Machado i in. 2009, nasilenie 1,0 — w liniowym RGB
MACHADO = {
    "protanopia": ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998)),
    "deuteranopia": ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881)),
    "tritanopia": ((1.255528, -0.076749, -0.178779), (-0.078411, 0.930809, 0.147602), (0.004733, 0.691367, 0.303900)),
}
NAZWY_CVD = {"protanopia": "protanopii", "deuteranopia": "deuteranopii", "tritanopia": "tritanopii"}


def norm(h) -> str | None:
    """'#1F2937' / "'#1f2937'" / '#1f2937ff' -> '#1f2937'; inne -> None."""
    if not isinstance(h, str):
        return None
    m = _HEX.match(h.strip().strip("'").strip())
    return "#" + m.group(1).lower() if m else None


def rgb(h: str):
    h = norm(h)
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def _lin(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _srgb(c: float) -> float:
    c = min(1.0, max(0.0, c))
    return 255.0 * (12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055)


def luminancja(kolor) -> float:
    r, g, b = rgb(kolor) if isinstance(kolor, str) else kolor
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def kontrast(a, b) -> float:
    """Współczynnik kontrastu WCAG 2.x (1..21)."""
    la, lb = luminancja(a), luminancja(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def lab(kolor):
    r, g, b = rgb(kolor) if isinstance(kolor, str) else kolor
    lin = (_lin(r), _lin(g), _lin(b))
    xyz = [sum(_M_XYZ[i][j] * lin[j] for j in range(3)) / _BIEL[i] for i in range(3)]
    d = 6 / 29
    f = [x ** (1 / 3) if x > d ** 3 else x / (3 * d * d) + 4 / 29 for x in xyz]
    return 116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])


def chroma(kolor) -> float:
    _, a, b = lab(kolor)
    return math.hypot(a, b)


def ciede2000(lab1, lab2) -> float:
    """ΔE00 (Sharma, Wu, Dalal 2005)."""
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cm = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360 if (a1p or b1) else 0.0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360 if (a2p or b2) else 0.0
    dLp, dCp = L2 - L1, C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    else:
        dhp = h2p - h1p
        if dhp > 180:
            dhp -= 360
        elif dhp < -180:
            dhp += 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp / 2))
    Lpm, Cpm = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0:
        hpm = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hpm = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        hpm = (h1p + h2p + 360) / 2
    else:
        hpm = (h1p + h2p - 360) / 2
    T = (1 - 0.17 * math.cos(math.radians(hpm - 30)) + 0.24 * math.cos(math.radians(2 * hpm))
         + 0.32 * math.cos(math.radians(3 * hpm + 6)) - 0.20 * math.cos(math.radians(4 * hpm - 63)))
    dth = 30 * math.exp(-(((hpm - 275) / 25) ** 2))
    Rc = 2 * math.sqrt(Cpm ** 7 / (Cpm ** 7 + 25 ** 7))
    Sl = 1 + 0.015 * (Lpm - 50) ** 2 / math.sqrt(20 + (Lpm - 50) ** 2)
    Sc = 1 + 0.045 * Cpm
    Sh = 1 + 0.015 * Cpm * T
    Rt = -math.sin(math.radians(2 * dth)) * Rc
    return math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh))


def cvd(kolor, typ: str):
    """Kolor widziany przy protanopii / deuteranopii / tritanopii (krotka RGB 0..255)."""
    r, g, b = rgb(kolor) if isinstance(kolor, str) else kolor
    lin = (_lin(r), _lin(g), _lin(b))
    m = MACHADO[typ]
    return tuple(_srgb(sum(m[i][j] * lin[j] for j in range(3))) for i in range(3))


def min_delta_e(kolory, typ_cvd: str | None = None):
    """Najbliższa para kolorów: (ΔE00, a, b) albo None dla < 2 kolorów."""
    unik = list(dict.fromkeys(k for k in (norm(x) for x in kolory) if k))
    if len(unik) < 2:
        return None
    labs = {k: lab(cvd(k, typ_cvd) if typ_cvd else k) for k in unik}
    best = None
    for i, a in enumerate(unik):
        for b in unik[i + 1:]:
            d = ciede2000(labs[a], labs[b])
            if best is None or d < best[0]:
                best = (d, a, b)
    return best


def odcien(kolor: str, procent: float) -> str:
    """Odcień koloru motywu jak w ThemeDataColor.Percent: >0 rozjaśnia do bieli, <0 przyciemnia."""
    r = rgb(kolor)
    if procent >= 0:
        r = tuple(c + (255 - c) * procent for c in r)
    else:
        r = tuple(c * (1 + procent) for c in r)
    return "#" + "".join(f"{int(round(min(255, max(0, c)))):02x}" for c in r)


def mieszaj(wierzch: str, spod: str, przezroczystosc: float) -> str:
    t = min(1.0, max(0.0, przezroczystosc))
    a, b = rgb(wierzch), rgb(spod)
    return "#" + "".join(f"{int(round(x * (1 - t) + y * t)):02x}" for x, y in zip(a, b))
