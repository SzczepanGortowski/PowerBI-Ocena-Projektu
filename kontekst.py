"""Kontekst reguł: raport, scalony motyw, wartości efektywne, teksty, kolory, oś czasu, obszar roboczy."""
from __future__ import annotations

import json
import re

from . import kolor
from .katalog import Problem
from .pbi.kaskada import Kaskada
from .pbi.raport import CHROM, Raport, Strona, Wizualizacja, literal, rodzina_fontu, wlasciwosci_ogolne

# Motyw domyślny Power BI (gdy raport nie ma motywu albo motyw nie podaje wartości)
KOLORY_PBI = ["#118dff", "#12239e", "#e66c37", "#6b007b", "#e044a7", "#744ec2", "#d9b300", "#d64550",
              "#197278", "#1aab40"]
KLASY_PBI = {
    "callout": {"fontSize": 45, "fontFace": "DIN", "color": "#252423"},
    "title": {"fontSize": 12, "fontFace": "DIN", "color": "#252423"},
    "header": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": "#252423"},
    "label": {"fontSize": 10, "fontFace": "Segoe UI", "color": "#252423"},
}

KOLOWE = {"pieChart", "donutChart"}
POLE_ZAMIAST_DLUGOSCI = {"pieChart", "donutChart", "treemap"}
MAPY = {"map", "azureMap", "filledMap", "shapeMap"}
SLUPKI_POZIOME = {"barChart", "clusteredBarChart", "hundredPercentStackedBarChart"}
SLUPKI_PIONOWE = {"columnChart", "clusteredColumnChart", "hundredPercentStackedColumnChart"}
LINIE = {"lineChart", "areaChart", "stackedAreaChart", "hundredPercentStackedAreaChart"}
DLUGOSC = SLUPKI_POZIOME | SLUPKI_PIONOWE | {"areaChart", "stackedAreaChart", "hundredPercentStackedAreaChart",
                                             "waterfallChart", "lineClusteredColumnComboChart",
                                             "lineStackedColumnComboChart", "ribbonChart"}
KARTEZJANSKIE = DLUGOSC | LINIE | {"lineChart", "scatterChart"}
KATEGORIE_KOLOREM = {"pieChart", "donutChart", "treemap", "funnel"}
ROLE_KAT = ("Category", "Axis", "Rows")
TEKSTOWE_MIARY = re.compile(r"(tytu[lł]|title|nag[lł][oó]wek|header|opis|tekst|text|od[sś]wie|refresh|stopka|"
                            r"footer|komunikat|etykiet)", re.I)
ROLE_MIAR = ("Y", "Y2", "Values", "Data")

CZAS = re.compile(r"(^|[\W_])(data|date|dzie[nń]|day|tydzie|week|miesi|month|kwarta|quarter|rok|year|okres|period|"
                  r"czas|time|godzin|hour|ym|yyyymm|rokmies)", re.I)
CIAGLE = re.compile(r"(odleg|promie|distance|wiek|age|sta[zż]|\bkm\b|\bm\b|metr|temperat|cena|price|godzin|hour)", re.I)
PORZADKOWE = re.compile(r"(przedzia|klaster|zakres|range|bucket|band|pasm|stopie|poziom|level|rozmiar|wielko|cykl|"
                        r"etap|faza|stage|krok|priorytet|ocena|rating|kwantyl|decyl|percentyl|grupa wiek|tier|segment wiel)",
                        re.I)
PY = re.compile(r"(\bPY\b|\bLY\b|\bPP\b|poprz|ubieg|rok temu|r/r|prior|previous|last year|year ago|\bLFL\b PY)", re.I)
PLAN = re.compile(r"(\bPL\b|\bBGT\b|\bBU\b|plan|bud[zż]et|target|\bcel\b|forecast|prognoz|\bFC\b)", re.I)


class Kontekst:
    def __init__(self, raport: Raport, model=None, konf: dict | None = None):
        self.raport = raport
        self.model = model
        self.konf = konf or {}
        self.progi = self.konf.get("progi", {})
        self.motyw = scalony_motyw(raport)
        self.kd = Kaskada(self.motyw)       # kaskada: wizualizacja -> motyw (bazowy + własny)

    def prog(self, nazwa, domyslny):
        return self.progi.get(nazwa, domyslny)

    # ------------------------------------------------------------ strony i obszar
    def strony(self) -> list[Strona]:
        """Strony do oceny: bez stron podpowiedzi (mała kanwa albo ukryta strona typu Tooltip)."""
        return [s for s in self.raport.strony
                if not ((s.w <= 700 and s.h <= 400) or (s.typ == "Tooltip" and s.ukryta))]

    def rail(self, s: Strona) -> float:
        """Prawa krawędź lewego raila: przyciski, obrazy i kształty w lewej ćwiartce kanwy."""
        lewe = [v for v in s.widoczne()
                if v.typ in ("actionButton", "image", "shape", "basicShape", "pageNavigator", "bookmarkNavigator")
                and v.x + v.w <= 0.25 * s.w]
        return max((v.x + v.w for v in lewe), default=0.0)

    def obszar(self, s: Strona):
        """Obszar roboczy: obwiednia treści bez raila, dociągnięta do krawędzi kanwy (margines 24)."""
        r = self.rail(s)
        tresc = [v for v in s.widoczne() if (v.klasa != "chrom" or v.typ == "textbox") and v.x + v.w / 2 > r]
        if not tresc:
            return (0.0, 0.0, s.w, s.h)
        x0 = max(0.0, min(v.x for v in tresc))
        y0 = max(0.0, min(v.y for v in tresc))
        x1 = min(s.w, max(max(v.x + v.w for v in tresc), s.w - 24))
        y1 = min(s.h, max(max(v.y + v.h for v in tresc), s.h - 24))
        return (x0, y0, x1, y1)

    def w_obszarze(self, s: Strona, v: Wizualizacja) -> bool:
        x0, _, x1, _ = self.obszar(s)
        cx = v.x + v.w / 2
        return x0 - 2 <= cx <= x1 + 2

    def dane(self, s: Strona) -> list[Wizualizacja]:
        """Wizualizacje z danymi (wykresy, tabele, karty) w obszarze roboczym."""
        return [v for v in s.widoczne() if v.klasa in ("wykres", "tabela", "karta") and self.w_obszarze(s, v)]

    def fragmentatory(self, s: Strona) -> list[Wizualizacja]:
        return [v for v in s.widoczne() if v.klasa == "filtr" and self.w_obszarze(s, v)]

    def tresc(self, s: Strona) -> list[Wizualizacja]:
        return self.dane(s) + self.fragmentatory(s) + [v for v in s.widoczne() if v.typ == "textbox" and self.w_obszarze(s, v)]

    # ------------------------------------------------------------ wartości efektywne
    def efekt(self, w, obiekt, wlasc, kontener=False, domyslna=None):
        return self.kd.efekt(w, obiekt, wlasc, kontener, domyslna)

    def wart(self, w, obiekt, wlasc, kontener=False, domyslna=None):
        return self.efekt(w, obiekt, wlasc, kontener, domyslna)[0]

    def kolory_danych(self) -> list[str]:
        dc = [kolor.norm(c) for c in (self.motyw.get("dataColors") or []) if isinstance(c, str)]
        return [c for c in dc if c] or list(KOLORY_PBI)

    def tlo_motywu(self) -> str:
        return kolor.norm(str(self.motyw.get("background", "#ffffff"))) or "#ffffff"

    def klasa_tekstu(self, nazwa: str) -> dict:
        """Klasa tekstu motywu (callout/title/header/label) z wartościami domyślnymi Power BI."""
        mot = self.motyw.get("textClasses") or {}
        tc = dict(KLASY_PBI["label"])
        tc.update(mot.get("label") or {})
        tc.update(KLASY_PBI.get(nazwa, {}))
        tc.update(mot.get(nazwa) or {})
        return tc

    # ------------------------------------------------------------ tytuł, tło, teksty
    def tytul_widoczny(self, w: Wizualizacja) -> bool:
        if w.klasa == "chrom":
            return bool(w.tytul_show)
        domyslnie = w.klasa in ("wykres", "tabela") and w.typ != "kpi"
        return self.wart(w, "title", "show", kontener=True, domyslna=domyslnie) is not False

    def tlo_strony(self, s: Strona) -> str | None:
        """Kolor tła strony; None, gdy tło to obraz (kolor znany dopiero z renderu)."""
        if s.tlo_obraz:
            return None
        return self.kd.kolor(s.tlo_kolor) or self.tlo_motywu()

    def tlo(self, s: Strona, w: Wizualizacja) -> str | None:
        """Kolor tła pod tekstem wizualizacji; None, gdy niewiadomy (przezroczysta nad obrazem tła)."""
        spod = self.tlo_strony(s)
        if w.typ == "actionButton":
            fill = wlasciwosci_ogolne(w.obiekty.get("fill"))
            if self.kd.wartosc(fill.get("show")) is True:
                c = self.kd.kolor(fill.get("fillColor"))
                tr = self.kd.wartosc(fill.get("transparency"))
                tr = float(tr) if isinstance(tr, (int, float)) else 0.0
                if c and tr < 50:
                    return kolor.mieszaj(c, spod, tr / 100) if spod else (c if tr == 0 else None)
            return spod
        pokaz = self.wart(w, "background", "show", kontener=True, domyslna=w.typ not in CHROM)
        if pokaz is not False:
            tr = self.wart(w, "background", "transparency", kontener=True, domyslna=0)
            tr = float(tr) if isinstance(tr, (int, float)) else 0.0
            c = self.wart(w, "background", "color", kontener=True)
            c = c if isinstance(c, str) and kolor.norm(c) else "#ffffff"
            if tr < 50:
                return kolor.mieszaj(c, spod, tr / 100) if spod else (c if tr == 0 else None)
        return spod

    def teksty(self, w: Wizualizacja) -> list[dict]:
        """Elementy tekstowe: {element, pt, kroj, kolor (None = warunkowy), pogrubiony}."""
        out = []

        def dodaj(element, klasa, obiekt, rozmiar="fontSize", kol_p="fontColor", kroj_p="fontFamily",
                  pokaz=True, kontener=False, pogrubiony=False):
            if obiekt and self.wart(w, obiekt, "show", kontener, pokaz) is False:
                return
            kl = self.klasa_tekstu(klasa)
            pt = self.wart(w, obiekt, rozmiar, kontener)
            kr = self.wart(w, obiekt, kroj_p, kontener)
            kv, skad = self.efekt(w, obiekt, kol_p, kontener)
            warunkowy = kv is None and skad != "domyślna"
            out.append({
                "element": element,
                "pt": float(pt) if isinstance(pt, (int, float)) and not isinstance(pt, bool) else float(kl.get("fontSize", 10)),
                "kroj": rodzina_fontu(kr) if isinstance(kr, str) else (rodzina_fontu(kl.get("fontFace")) or "Segoe UI"),
                "kolor": None if warunkowy else (kolor.norm(kv) if isinstance(kv, str) else None)
                or kolor.norm(str(kl.get("color") or self.motyw.get("foreground") or "#252423")),
                "warunkowy": warunkowy,
                "pogrubiony": pogrubiony,
            })

        if self.tytul_widoczny(w) and w.klasa != "chrom":
            dodaj("tytuł", "title", "title", kontener=True,
                  pogrubiony=bool(self.wart(w, "title", "bold", kontener=True, domyslna=False)))
        t = w.typ
        if w.klasa == "wykres" and t not in POLE_ZAMIAST_DLUGOSCI and t not in MAPY:
            dodaj("oś kategorii", "label", "categoryAxis", kol_p="labelColor")
            dodaj("oś wartości", "label", "valueAxis", kol_p="labelColor")
            dodaj("etykiety danych", "label", "labels", kol_p="color", pokaz=False)
            dodaj("legenda", "label", "legend", kol_p="labelColor", pokaz=w.ma_serie or self.liczba_miar(w) > 1)
        elif t in POLE_ZAMIAST_DLUGOSCI:
            dodaj("etykiety danych", "label", "labels", kol_p="color")
            dodaj("legenda", "label", "legend", kol_p="labelColor")
        elif t == "cardVisual":
            dodaj("wartość KPI", "callout", "value", pogrubiony=True)
            dodaj("etykieta KPI", "label", "label")
        elif t == "card":
            dodaj("wartość KPI", "callout", "labels", kol_p="color", pogrubiony=True)
            dodaj("etykieta KPI", "label", "categoryLabels", kol_p="color")
        elif t == "multiRowCard":
            dodaj("wartości", "label", "dataLabels", kol_p="color")
            dodaj("etykiety", "label", "categoryLabels", kol_p="color")
        elif w.klasa == "tabela":
            dodaj("nagłówki kolumn", "label", "columnHeaders")
            dodaj("wartości", "label", "values", kol_p="fontColorPrimary")
            if t in ("pivotTable", "matrix"):
                dodaj("nagłówki wierszy", "label", "rowHeaders")
        elif w.klasa == "filtr":
            dodaj("nagłówek fragmentatora", "header", "header", rozmiar="textSize")
            dodaj("pozycje fragmentatora", "label", "items", rozmiar="textSize")
        elif t == "actionButton":
            dodaj("tekst przycisku", "label", "text", pokaz=False)
        elif t == "textbox":
            for par in (wlasciwosci_ogolne(w.obiekty.get("general")).get("paragraphs") or []):
                for run in (par or {}).get("textRuns", []) or []:
                    st = run.get("textStyle", {}) or {}
                    if not str(run.get("value", "")).strip():
                        continue
                    m = re.match(r"^\s*(\d+(?:\.\d+)?)", str(st.get("fontSize", "")))
                    out.append({
                        "element": "pole tekstowe", "pt": float(m.group(1)) if m else 10.0,
                        "kroj": rodzina_fontu(st.get("fontFamily")) or "Segoe UI",
                        "kolor": kolor.norm(st.get("color") or "") or kolor.norm(str(self.motyw.get("foreground") or "#252423")),
                        "warunkowy": False,
                        "pogrubiony": str(st.get("fontWeight", "")).lower() in ("bold", "600", "700", "bolder"),
                    })
        return out

    # ------------------------------------------------------------ dane wizualizacji
    def kategorie(self, w: Wizualizacja) -> list[dict]:
        return w.projekcje_roli(*ROLE_KAT)

    def miary(self, w: Wizualizacja) -> list[str]:
        return [p.get("queryRef") or "?" for p in w.projekcje_roli(*ROLE_MIAR)]

    def liczba_miar(self, w: Wizualizacja) -> int:
        return len(w.projekcje_roli(*ROLE_MIAR))

    def kolory_miar_nadpisane(self, w: Wizualizacja) -> dict:
        out = {}
        for e in w.obiekty.get("dataPoint", []) or []:
            sel = (e or {}).get("selector") or {}
            fill = ((e or {}).get("properties") or {}).get("fill")
            if sel.get("metadata") and fill is not None and "data" not in sel:
                c = self.kd.kolor(fill)
                if c:
                    out[sel["metadata"]] = c
        return out

    def kolory_kategorii(self, w: Wizualizacja) -> set:
        """Kolory nadane pojedynczym kategoriom (selektor danych) — „tęczowe” kolorowanie."""
        out = set()
        for e in w.obiekty.get("dataPoint", []) or []:
            sel = (e or {}).get("selector") or {}
            fill = ((e or {}).get("properties") or {}).get("fill")
            if "data" in sel and fill is not None:
                c = self.kd.kolor(fill)
                if c:
                    out.add(c)
        return out

    def kolory_serii(self, w: Wizualizacja):
        """(kolory, założone): założone=True, gdy liczba kategorii serii nie wynika z definicji (przyjęto 6)."""
        if w.klasa != "wykres" or w.typ in MAPY:
            return None
        paleta = self.kolory_danych()
        if w.ma_serie or w.typ in KOLOWE or w.typ in ("treemap", "funnel"):
            return paleta[:min(6, len(paleta))], True
        miary = self.miary(w)
        if not miary:
            return None
        nad = self.kolory_miar_nadpisane(w)
        if len(miary) == 1:
            dom = self.wart(w, "dataPoint", "defaultColor")
            return [nad.get(miary[0]) or (dom if isinstance(dom, str) and kolor.norm(dom) else paleta[0])], False
        return [nad.get(m) or paleta[i % len(paleta)] for i, m in enumerate(miary)], False

    def kolory_miar(self, w: Wizualizacja) -> dict:
        """miara -> kolor dla wykresów bez roli Series (spójność kolor ↔ miara)."""
        if w.klasa != "wykres" or w.ma_serie or w.typ in MAPY:
            return {}
        k = self.kolory_serii(w)
        if not k or k[1]:
            return {}
        return {m: kolor.norm(c) for m, c in zip(self.miary(w), k[0])}

    def os_wartosci(self, w: Wizualizacja) -> dict:
        return {
            "pokazana": self.wart(w, "valueAxis", "show", domyslna=True) is not False,
            "start": self.wart(w, "valueAxis", "start"),
            "koniec": self.wart(w, "valueAxis", "end"),
            "skala": self.wart(w, "valueAxis", "axisScale"),
            "siatka": self.wart(w, "valueAxis", "gridlineShow", domyslna=True) is not False,
            "druga": bool(w.projekcje_roli("Y2")) or self.wart(w, "valueAxis", "secShow", domyslna=False) is True,
        }

    def ma_alt_text(self, w: Wizualizacja) -> bool:
        """Tekst alternatywny stały albo dynamiczny (miara DAX — najlepsza praktyka)."""
        v = wlasciwosci_ogolne(w.kontener.get("general")).get("altText")
        if isinstance(v, dict) and isinstance(v.get("expr"), dict) and "Literal" not in v["expr"]:
            return True
        return isinstance(w.alt_text, str) and bool(w.alt_text.strip())

    def karta_tekstowa(self, w: Wizualizacja) -> bool:
        """Karta użyta jako tytuł, stopka albo komunikat (wartość tekstowa, nie KPI)."""
        miary = self.miary(w)
        if miary and all(TEKSTOWE_MIARY.search(m.split(".")[-1]) for m in miary):
            return True
        if self.model is not None:
            for p in w.projekcje_roli(*ROLE_MIAR):
                pole = p.get("pole") or {}
                mi = self.model.miara(pole.get("nazwa") or "") if pole.get("rodzaj") == "Measure" else None
                if mi is not None and (mi.format or "") == "" and re.search(r'"|FORMAT\s*\(|CONCATENATE|&', mi.wyrazenie or ""):
                    return True
        bez_etykiety = self.wart(w, "label", "show", domyslna=True) is False or \
            self.wart(w, "categoryLabels", "show", domyslna=True) is False
        return bez_etykiety and w.h < 70 and w.w > 3 * w.h and bool(TEKSTOWE_MIARY.search(w.nazwa))

    def etykiety_danych(self, w: Wizualizacja) -> bool:
        domyslnie = w.typ in POLE_ZAMIAST_DLUGOSCI
        return self.wart(w, "labels", "show", domyslna=domyslnie) is True

    # ------------------------------------------------------------ czas i ciągłość
    def _kolumna_modelu(self, pole: dict):
        if self.model is None or not pole.get("encja") or not pole.get("nazwa"):
            return None
        return self.model.kolumna(pole["encja"], pole["nazwa"])

    def czy_czas(self, projekcja: dict) -> bool:
        pole = projekcja.get("pole") or {}
        nazwa = pole.get("nazwa") or ""
        if pole.get("rodzaj") == "HierarchyLevel":
            return True if not nazwa else bool(CZAS.search(nazwa)) or nazwa in ("Year", "Quarter", "Month", "Day")
        k = self._kolumna_modelu(pole)
        if k is not None:
            if (k.typ_danych or "").lower() == "datetime":
                return True
            t = self.model.tabela(pole["encja"])
            if t is not None and (t.kategoria or "").lower() == "time" and CZAS.search(nazwa):
                return True
        return bool(CZAS.search(nazwa) or CZAS.search(projekcja.get("queryRef") or ""))

    def czy_ciagla(self, projekcja: dict) -> bool:
        """Kategoria liczbowa (odległość, wiek, godzina) — linia między punktami ma sens."""
        pole = projekcja.get("pole") or {}
        k = self._kolumna_modelu(pole)
        if k is not None and (k.typ_danych or "").lower() in ("int64", "double", "decimal"):
            return True
        return bool(CIAGLE.search(pole.get("nazwa") or ""))

    def czy_porzadkowa(self, projekcja: dict) -> bool:
        """Kategoria o naturalnej kolejności (przedziały, etapy, poziomy) — sortowanie po nazwie jest właściwe."""
        pole = projekcja.get("pole") or {}
        k = self._kolumna_modelu(pole)
        if k is not None and k.sortuj_wg:
            return True
        return bool(PORZADKOWE.search(pole.get("nazwa") or ""))

    # ------------------------------------------------------------ znaleziska
    @staticmethod
    def problem_wiz(s: Strona, w: Wizualizacja, rid: str, opis: str, waga: str = "") -> Problem:
        return Problem(rid, opis, strona=s.tytul, obiekt=w.etykieta, typ_obiektu="wizualizacja", waga=waga,
                       id_strony=s.nazwa, id_wizualizacji=w.nazwa)

    @staticmethod
    def problem_str(s: Strona, rid: str, opis: str, waga: str = "") -> Problem:
        return Problem(rid, opis, strona=s.tytul, typ_obiektu="strona", waga=waga, id_strony=s.nazwa)

    @staticmethod
    def problem_rap(rid: str, opis: str, obiekt: str = "", waga: str = "") -> Problem:
        return Problem(rid, opis, obiekt=obiekt, typ_obiektu="raport", waga=waga)


def scalony_motyw(raport: Raport) -> dict:
    """Motyw bazowy (SharedResources/BaseThemes) z nałożonym motywem niestandardowym."""
    baza = {}
    if raport.motyw_bazowy and raport.zrodlo:
        for rel in (f"StaticResources/SharedResources/BaseThemes/{raport.motyw_bazowy}.json",
                    f"StaticResources/SharedResources/BaseThemes/{raport.motyw_bazowy}"):
            try:
                d = raport.zrodlo.json(rel)
            except (json.JSONDecodeError, UnicodeDecodeError, OSError):
                d = None
            if isinstance(d, dict):
                baza = d
                break
    wlasny = raport.motyw if isinstance(raport.motyw, dict) else {}
    out = dict(baza)
    for k, v in wlasny.items():
        if k == "textClasses" and isinstance(out.get(k), dict) and isinstance(v, dict):
            tc = {kl: dict(x) for kl, x in out[k].items() if isinstance(x, dict)}
            for kl, x in v.items():
                tc.setdefault(kl, {}).update(x if isinstance(x, dict) else {})
            out[k] = tc
        elif k == "visualStyles" and isinstance(out.get(k), dict) and isinstance(v, dict):
            out[k] = {**out[k], **v}
        else:
            out[k] = v
    return out


def nazwa_motywu(raport: Raport) -> str:
    if raport.motyw_plik:
        return str(raport.motyw_plik)
    if raport.motyw_bazowy:
        return f"{raport.motyw_bazowy} (motyw bazowy)"
    return "domyślny Power BI"


def literal_liczba(v):
    x = literal(v) if isinstance(v, dict) else v
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else None
