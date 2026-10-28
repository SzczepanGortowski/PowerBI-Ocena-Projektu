"""Odczyt definicji raportu Power BI — tylko odczyt, nic nie zapisuje.

Obsługiwane formaty:
- PBIR (folder *.Report z definition/, projekt .pbip) — format zapisu projektów Power BI,
- PBIR-legacy (folder *.Report z report.json) i .pbix (Report/Layout albo Report/definition/).
Wszystkie trzy są sprowadzane do tej samej struktury: Raport -> Strona -> Wizualizacja.
"""
from __future__ import annotations

import json
import re
import zipfile
from datetime import datetime
from pathlib import Path

CHROM = {"shape", "basicShape", "image", "actionButton", "textbox", "pageNavigator",
         "bookmarkNavigator", "group"}
FILTRY = {"slicer", "listSlicer", "advancedSlicerVisual", "textSlicer", "buttonSlicer"}
KARTY = {"card", "cardVisual", "multiRowCard", "kpi", "gauge"}
TABELE = {"tableEx", "pivotTable", "table", "matrix"}
WYKRESY_KOLOWE = {"pieChart", "donutChart", "funnel", "gauge", "treemap"}
ROLE_KATEGORII = {"Category", "Rows", "Columns", "Series", "Legend", "Group", "Details", "Axis",
                  "Location", "Latitude", "Longitude"}


# ---------------------------------------------------------------- wartości PBIR

def literal(v):
    """Wartość literału PBIR albo motywu: '14D' -> 14.0, "'#1F2937'" -> '#1F2937', 'true' -> True."""
    if isinstance(v, dict):
        e = v.get("expr", v)
        if isinstance(e, dict) and "Literal" in e:
            return literal(e["Literal"].get("Value"))
        return None
    if isinstance(v, (int, float, bool)):
        return v
    if not isinstance(v, str):
        return None
    s = v.strip()
    if s in ("true", "false"):
        return s == "true"
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)[DLM]?", s)
    if m:
        return float(m.group(1))
    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        return s[1:-1].replace("''", "'")
    return s


def rodzina_fontu(v) -> str | None:
    """Pierwsza rodzina z listy: "'Segoe UI', wf_segoe-ui_normal, ..." -> 'Segoe UI'."""
    s = literal(v) if isinstance(v, dict) else v
    if not isinstance(s, str) or not s.strip():
        return None
    return s.split(",")[0].strip().strip("'\"").strip() or None


def wlasciwosci_ogolne(lista) -> dict:
    """Scalone wpisy obiektu bez selektora (albo selector.id == 'default')."""
    out = {}
    if not isinstance(lista, list):
        return out
    for e in lista:
        if not isinstance(e, dict):
            continue
        sel = e.get("selector")
        if not sel or (sel.get("id") == "default" and len(sel) == 1):
            out.update(e.get("properties") or {})
    return out


# ---------------------------------------------------------------- pola modelu w JSON

def _encja(expr, aliasy):
    if not isinstance(expr, dict):
        return None
    sr = expr.get("SourceRef")
    if isinstance(sr, dict):
        return sr.get("Entity") or (aliasy or {}).get(sr.get("Source"))
    return None


def zbierz_pola(obj, aliasy=None, out=None):
    """Wszystkie odwołania do modelu: (encja, nazwa, 'Column'|'Measure')."""
    if out is None:
        out = []
    if isinstance(obj, dict):
        if isinstance(obj.get("From"), list):
            aliasy = dict(aliasy or {})
            for f in obj["From"]:
                if isinstance(f, dict) and f.get("Name") and f.get("Entity"):
                    aliasy[f["Name"]] = f["Entity"]
        for rodzaj in ("Column", "Measure"):
            w = obj.get(rodzaj)
            if isinstance(w, dict) and "Property" in w:
                e = _encja(w.get("Expression"), aliasy)
                if e:
                    out.append((e, w["Property"], rodzaj))
        for v in obj.values():
            zbierz_pola(v, aliasy, out)
    elif isinstance(obj, list):
        for v in obj:
            zbierz_pola(v, aliasy, out)
    return out


def opis_pola(field: dict, aliasy=None) -> dict:
    """Projekcja -> {rodzaj, encja, nazwa, agregacja}."""
    if not isinstance(field, dict):
        return {"rodzaj": "?"}
    if "Aggregation" in field:
        a = field["Aggregation"]
        wew = opis_pola(a.get("Expression"), aliasy)
        return {"rodzaj": "Aggregation", "encja": wew.get("encja"), "nazwa": wew.get("nazwa"),
                "agregacja": a.get("Function")}
    for rodzaj in ("Measure", "Column"):
        if rodzaj in field:
            w = field[rodzaj]
            return {"rodzaj": rodzaj, "encja": _encja(w.get("Expression"), aliasy), "nazwa": w.get("Property")}
    if "HierarchyLevel" in field:
        return {"rodzaj": "HierarchyLevel", "nazwa": field["HierarchyLevel"].get("Level")}
    if "NativeVisualCalculation" in field:
        return {"rodzaj": "VisualCalculation", "nazwa": field["NativeVisualCalculation"].get("Name")}
    return {"rodzaj": next(iter(field), "?")}


# ---------------------------------------------------------------- źródło plików

class Zrodlo:
    """Pliki raportu z folderu albo z archiwum .pbix (ścieżki zawsze z '/')."""

    def __init__(self, folder: Path | None = None, archiwum: Path | None = None, prefiks: str = ""):
        self.folder = folder
        self.prefiks = prefiks
        self.zip = zipfile.ZipFile(archiwum) if archiwum else None
        self.archiwum = archiwum

    def czytaj(self, rel: str) -> bytes | None:
        if self.zip:
            try:
                return self.zip.read(self.prefiks + rel)
            except KeyError:
                return None
        p = self.folder / rel
        return p.read_bytes() if p.is_file() else None

    def json(self, rel: str):
        b = self.czytaj(rel)
        if b is None:
            return None
        return json.loads(_dekoduj(b))

    def lista(self, prefiks: str) -> list[str]:
        if self.zip:
            pel = self.prefiks + prefiks
            return [n[len(self.prefiks):] for n in self.zip.namelist() if n.startswith(pel) and not n.endswith("/")]
        baza = self.folder / prefiks
        if not baza.exists():
            return []
        return [p.relative_to(self.folder).as_posix() for p in baza.rglob("*") if p.is_file()]

    def czas_zapisu(self) -> datetime | None:
        if self.zip:
            return datetime.fromtimestamp(self.archiwum.stat().st_mtime)
        czasy = [p.stat().st_mtime for p in self.folder.rglob("*.json")]
        return datetime.fromtimestamp(max(czasy)) if czasy else None


def _dekoduj(b: bytes) -> str:
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return b.decode("utf-16")
    if len(b) > 1 and b[1:2] == b"\x00":
        return b.decode("utf-16-le")
    return b.decode("utf-8-sig")


# ---------------------------------------------------------------- struktura

class Wizualizacja:
    def __init__(self, nazwa, typ, poz, obiekty, kontener, projekcje, surowe, ukryta=False,
                 grupa=None, plik="", aliasy=None):
        self.nazwa = nazwa
        self.typ = typ
        self.x = float(poz.get("x", 0) or 0)
        self.y = float(poz.get("y", 0) or 0)
        self.w = float(poz.get("width", 0) or 0)
        self.h = float(poz.get("height", 0) or 0)
        self.z = float(poz.get("z", 0) or 0)
        self.obiekty = obiekty or {}
        self.kontener = kontener or {}
        self.projekcje = projekcje          # rola -> [ {pole, queryRef} ]
        self.surowe = surowe
        self.ukryta = bool(ukryta)
        self.grupa = grupa
        self.plik = plik
        self.pola = zbierz_pola(surowe, aliasy)
        tyt = wlasciwosci_ogolne(self.kontener.get("title"))
        self.tytul_tekst = literal(tyt.get("text")) if "text" in tyt else None
        self.tytul_show = literal(tyt.get("show")) if "show" in tyt else None
        gen = wlasciwosci_ogolne(self.kontener.get("general"))
        self.alt_text = literal(gen.get("altText")) if "altText" in gen else None

    @property
    def klasa(self):
        if self.typ in CHROM:
            return "chrom"
        if self.typ in FILTRY:
            return "filtr"
        if self.typ in KARTY:
            return "karta"
        if self.typ in TABELE:
            return "tabela"
        return "wykres"

    @property
    def danych(self) -> bool:
        return self.klasa in ("karta", "tabela", "wykres", "filtr")

    @property
    def etykieta(self) -> str:
        t = self.tytul_tekst if isinstance(self.tytul_tekst, str) and self.tytul_tekst.strip() else None
        return f"{t} ({self.typ})" if t else f"{self.nazwa} ({self.typ})"

    def projekcje_roli(self, *role):
        out = []
        for r in role:
            out += self.projekcje.get(r, [])
        return out

    @property
    def ma_serie(self):
        return bool(self.projekcje_roli("Series", "Legend"))

    @property
    def prostokat(self):
        return (self.x, self.y, self.x + self.w, self.y + self.h)


class Strona:
    def __init__(self, nazwa, tytul, w, h, ukryta, typ, obiekty, wizualizacje, filtry=None):
        self.nazwa = nazwa
        self.tytul = tytul or nazwa
        self.w = float(w or 1280)
        self.h = float(h or 720)
        self.ukryta = ukryta
        self.typ = typ                   # None | 'Tooltip' | 'Drillthrough'
        self.obiekty = obiekty or {}
        self.wizualizacje: list[Wizualizacja] = wizualizacje
        self.filtry = filtry or []
        tlo = wlasciwosci_ogolne(self.obiekty.get("background"))
        self.tlo_obraz = None
        im = tlo.get("image")
        if isinstance(im, dict):
            img = im.get("image", im)
            url = (img.get("url") or {}).get("expr", {}).get("ResourcePackageItem", {}) if isinstance(img, dict) else {}
            self.tlo_obraz = url.get("ItemName") or literal(img.get("name")) if isinstance(img, dict) else None
        self.tlo_kolor = tlo.get("color")

    @property
    def podpowiedz(self):
        return self.typ == "Tooltip" or (self.h <= 400 and self.w <= 600)

    def widoczne(self):
        return [v for v in self.wizualizacje if not v.ukryta and v.typ != "group"]


class Raport:
    def __init__(self):
        self.nazwa = ""
        self.sciezka = ""
        self.format = ""
        self.zrodlo: Zrodlo | None = None
        self.motyw = None
        self.motyw_plik = None
        self.motyw_bazowy = None
        self.strony: list[Strona] = []
        self.zasoby: dict[str, str] = {}             # nazwa zasobu -> typ
        self.wizualizacje_niestandardowe: list[str] = []
        self.miary_raportu: set[tuple[str, str]] = set()
        self.filtry: list = []
        self.zakladki = 0
        self.model_lokalny = None                    # True: .SemanticModel obok; False: połączenie na żywo
        self.zapisano: datetime | None = None

    def zasob(self, nazwa: str) -> bytes | None:
        if not nazwa or not self.zrodlo:
            return None
        return self.zrodlo.czytaj(f"StaticResources/RegisteredResources/{nazwa}")

    def wszystkie_wizualizacje(self):
        for s in self.strony:
            for v in s.wizualizacje:
                yield s, v


# ---------------------------------------------------------------- otwieranie

def otworz(sciezka: str | Path) -> Raport:
    p = Path(sciezka).resolve()
    r = Raport()
    r.sciezka = str(p)
    if p.suffix.lower() == ".pbip":
        r.nazwa = p.stem
        d = json.loads(p.read_text(encoding="utf-8-sig"))
        rel = None
        for a in d.get("artifacts", []):
            rel = (a.get("report") or {}).get("path") or rel
        p = (p.parent / (rel or f"{p.stem}.Report")).resolve()
    if p.suffix.lower() in (".pbix", ".pbit"):
        r.nazwa = r.nazwa or p.stem
        zr = Zrodlo(archiwum=p, prefiks="Report/")
        r.zrodlo = zr
        r.model_lokalny = any(n.startswith("DataModel") for n in zr.zip.namelist())
        if zr.czytaj("definition/report.json") is not None:
            r.format = "PBIX (PBIR)"
            _czytaj_pbir(r, zr)
        else:
            r.format = "PBIX"
            _czytaj_legacy(r, zr, "Layout")
        r.zapisano = zr.czas_zapisu()
        return r
    if p.is_dir() and not p.name.endswith(".Report"):
        kand = sorted(p.glob("*.Report"))
        if len(kand) == 1:
            p = kand[0]
        elif (p / "definition" / "report.json").exists() or (p / "report.json").exists():
            pass
        else:
            raise ValueError(f"Nie znaleziono folderu *.Report w {p}")
    if not p.is_dir():
        raise ValueError(f"Nieobsługiwana ścieżka raportu: {p}")
    r.nazwa = r.nazwa or p.name.removesuffix(".Report")
    zr = Zrodlo(folder=p)
    r.zrodlo = zr
    pbir = zr.json("definition.pbir") or {}
    ref = pbir.get("datasetReference") or {}
    r.model_lokalny = True if "byPath" in ref else (False if "byConnection" in ref else None)
    if zr.czytaj("definition/report.json") is not None:
        r.format = "PBIR"
        _czytaj_pbir(r, zr)
    elif zr.czytaj("report.json") is not None:
        r.format = "PBIR-legacy"
        _czytaj_legacy(r, zr, "report.json")
    else:
        raise ValueError(f"Brak definition/report.json ani report.json w {p}")
    r.zapisano = zr.czas_zapisu()
    return r


def _motyw(r: Raport, zr: Zrodlo, kolekcja: dict):
    ct = (kolekcja or {}).get("customTheme")
    if ct:
        r.motyw_plik = ct.get("name")
        for rel in (f"StaticResources/RegisteredResources/{ct.get('name')}",
                    f"StaticResources/RegisteredResources/{ct.get('name')}.json"):
            try:
                d = zr.json(rel)
            except (json.JSONDecodeError, UnicodeDecodeError):
                d = None
            if d is not None:
                r.motyw = d
                break
    bt = (kolekcja or {}).get("baseTheme")
    if bt:
        r.motyw_bazowy = bt.get("name")


def _czytaj_pbir(r: Raport, zr: Zrodlo):
    rj = zr.json("definition/report.json") or {}
    _motyw(r, zr, rj.get("themeCollection"))
    for pkg in rj.get("resourcePackages", []) or []:
        for it in pkg.get("items", []) or []:
            r.zasoby[it.get("name")] = it.get("type")
        if pkg.get("type") == "CustomVisual":
            r.wizualizacje_niestandardowe.append(pkg.get("name"))
    r.wizualizacje_niestandardowe += list(rj.get("publicCustomVisuals", []) or [])
    r.filtry = (rj.get("filterConfig") or {}).get("filters", []) or []
    ext = zr.json("definition/reportExtensions.json") or {}
    for ent in ext.get("entities", []) or []:
        for m in ent.get("measures", []) or []:
            r.miary_raportu.add((ent.get("name"), m.get("name")))
    r.zakladki = len([n for n in zr.lista("definition/bookmarks/") if n.endswith(".bookmark.json")])

    pliki = zr.lista("definition/pages/")
    strony_json = {n.split("/")[2]: n for n in pliki if n.endswith("/page.json") and n.count("/") == 3}
    kolejnosc = (zr.json("definition/pages/pages.json") or {}).get("pageOrder", []) or []
    nazwy = [n for n in kolejnosc if n in strony_json] + sorted(n for n in strony_json if n not in kolejnosc)
    for folder_strony in nazwy:
        pj = zr.json(strony_json[folder_strony]) or {}
        wiz = []
        for vf in sorted(n for n in pliki if n.startswith(f"definition/pages/{folder_strony}/visuals/")
                         and n.endswith("/visual.json")):
            try:
                d = zr.json(vf) or {}
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            v = d.get("visual") or {}
            typ = v.get("visualType") or ("group" if "visualGroup" in d else "?")
            projekcje = {}
            for rola, st in ((v.get("query") or {}).get("queryState") or {}).items():
                projekcje[rola] = [{"pole": opis_pola(p.get("field")), "queryRef": p.get("queryRef")}
                                   for p in (st or {}).get("projections", []) or []]
            wiz.append(Wizualizacja(d.get("name", vf.split("/")[-2]), typ, d.get("position") or {},
                                    v.get("objects"), v.get("visualContainerObjects"), projekcje, d,
                                    ukryta=d.get("isHidden"), grupa=d.get("parentGroupName"), plik=vf))
        typ_strony = (pj.get("pageBinding") or {}).get("type")
        r.strony.append(Strona(pj.get("name", folder_strony), pj.get("displayName"), pj.get("width"),
                               pj.get("height"), pj.get("visibility") == "HiddenInViewMode", typ_strony,
                               pj.get("objects"), wiz, (pj.get("filterConfig") or {}).get("filters", [])))


def _json_str(s, domyslny=None):
    if isinstance(s, (dict, list)):
        return s
    try:
        return json.loads(s) if s else domyslny
    except (json.JSONDecodeError, TypeError):
        return domyslny


def _czytaj_legacy(r: Raport, zr: Zrodlo, plik: str):
    lay = zr.json(plik) or {}
    cfg = _json_str(lay.get("config"), {}) or {}
    _motyw(r, zr, cfg.get("themeCollection"))
    for pkg in lay.get("resourcePackages", []) or []:
        rp = pkg.get("resourcePackage", pkg)
        for it in rp.get("items", []) or []:
            r.zasoby[it.get("name")] = it.get("type")
        if rp.get("type") in (0, "CustomVisual") and rp.get("name") not in ("RegisteredResources", "SharedResources"):
            r.wizualizacje_niestandardowe.append(rp.get("name"))
    r.wizualizacje_niestandardowe += list(lay.get("publicCustomVisuals", []) or cfg.get("publicCustomVisuals", []) or [])
    r.filtry = _json_str(lay.get("filters"), []) or []
    for ent in (cfg.get("modelExtensions") or [{}])[0].get("entities", []) if cfg.get("modelExtensions") else []:
        for m in ent.get("measures", []) or []:
            r.miary_raportu.add((ent.get("name"), m.get("name")))
    r.zakladki = len(cfg.get("bookmarks", []) or [])

    for sec in sorted(lay.get("sections", []) or [], key=lambda s: s.get("ordinal", 0)):
        scfg = _json_str(sec.get("config"), {}) or {}
        wiz = []
        for vc in sec.get("visualContainers", []) or []:
            c = _json_str(vc.get("config"), {}) or {}
            poz = ((c.get("layouts") or [{}])[0].get("position")) or {
                "x": vc.get("x"), "y": vc.get("y"), "z": vc.get("z"),
                "width": vc.get("width"), "height": vc.get("height")}
            sv = c.get("singleVisual")
            if sv is None:
                typ = "group" if "singleVisualGroup" in c else "?"
                sv = {}
            else:
                typ = sv.get("visualType", "?")
            pq = sv.get("prototypeQuery") or {}
            aliasy = {f.get("Name"): f.get("Entity") for f in pq.get("From", []) or []}
            select = {s.get("Name"): s for s in pq.get("Select", []) or []}
            projekcje = {}
            for rola, lst in (sv.get("projections") or {}).items():
                projekcje[rola] = [{"pole": opis_pola(select.get(p.get("queryRef")), aliasy),
                                    "queryRef": p.get("queryRef")} for p in lst or []]
            surowe = {"config": c, "filters": _json_str(vc.get("filters"), [])}
            ukryta = c.get("isHidden") or (sv.get("display") or {}).get("mode") == "hidden"
            wiz.append(Wizualizacja(c.get("name", ""), typ, poz, sv.get("objects"), sv.get("vcObjects"),
                                    projekcje, surowe, ukryta=ukryta,
                                    grupa=c.get("parentGroupName"), aliasy=aliasy))
        typ_strony = "Tooltip" if (scfg.get("type") == 2 or (scfg.get("pageBinding") or {}).get("type") == "Tooltip") else None
        r.strony.append(Strona(sec.get("name"), sec.get("displayName"), sec.get("width"), sec.get("height"),
                               scfg.get("visibility") == 1, typ_strony, scfg.get("objects"), wiz,
                               _json_str(sec.get("filters"), [])))
