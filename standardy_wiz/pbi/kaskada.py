"""Wartości efektywne formatowania: wizualizacja → motyw (visualStyles typu i '*') → wartość domyślna."""
from __future__ import annotations

from .. import kolor
from .raport import Wizualizacja, literal, wlasciwosci_ogolne


class Kaskada:
    def __init__(self, motyw: dict | None):
        self.motyw = motyw or {}

    def z_motywu(self, typ, obiekt, wlasc):
        vs = self.motyw.get("visualStyles", {}) or {}
        for t in (typ, "*"):
            lst = ((vs.get(t) or {}).get("*") or {}).get(obiekt)
            if isinstance(lst, list) and lst and isinstance(lst[0], dict) and wlasc in lst[0]:
                return lst[0][wlasc]
        return None

    def efekt(self, wiz: Wizualizacja, obiekt, wlasc, kontener=False, domyslna=None):
        """(wartość, skąd): skąd = 'wizualizacja' | 'motyw' | 'domyślna'."""
        zr = wiz.kontener if kontener else wiz.obiekty
        w = wlasciwosci_ogolne(zr.get(obiekt))
        if wlasc in w:
            return self.wartosc(w[wlasc]), "wizualizacja"
        v = self.z_motywu(wiz.typ, obiekt, wlasc)
        if v is not None:
            return self.wartosc(v), "motyw"
        return domyslna, "domyślna"

    def wartosc(self, v):
        if isinstance(v, dict):
            k = self.kolor(v)
            if k:
                return k
            return None if "solid" in v else literal(v)
        return v

    def kolory_danych(self) -> list[str]:
        dc = [kolor.norm(c) for c in (self.motyw.get("dataColors") or []) if isinstance(c, str)]
        return [c for c in dc if c] or ["#118dff"]

    def kolor(self, v) -> str | None:
        """Kolor stały -> '#rrggbb'; kolor dynamiczny (z miary albo reguły) -> None."""
        if v is None:
            return None
        if isinstance(v, str):
            return kolor.norm(v)
        if isinstance(v, dict):
            if "solid" in v:
                return self.kolor(v["solid"].get("color"))
            e = v.get("expr", v)
            if isinstance(e, dict):
                if "Literal" in e:
                    return kolor.norm(literal(e["Literal"].get("Value")) or "")
                if "ThemeDataColor" in e:
                    # ColorId 0 = tło, 1 = pierwszy plan, 2.. = dataColors[ColorId-2]; Percent = odcień
                    td = e["ThemeDataColor"]
                    cid = int(td.get("ColorId", 0) or 0)
                    baza = [self.motyw.get("background", "#ffffff"), self.motyw.get("foreground", "#252423")] \
                        + self.kolory_danych()
                    if cid >= len(baza) or not kolor.norm(str(baza[cid])):
                        return None
                    return kolor.odcien(kolor.norm(str(baza[cid])), float(td.get("Percent", 0) or 0))
        return None
