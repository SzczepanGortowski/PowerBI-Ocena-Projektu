"""Uruchomienie reguł, wynik dla panelu (wynik.json) i lista zadań (Markdown) dla wybranych standardów."""
from __future__ import annotations

import json
import traceback
from datetime import datetime
from pathlib import Path

from . import (reguly_dashboard, reguly_ibcs, reguly_microsoft, reguly_minimalizm,  # noqa: F401 (rejestracja)
               reguly_percepcja, reguly_spojnosc, reguly_uklad, reguly_wcag)
from .katalog import DOMYSLNE, FUNKCJE, PROFILE, REGULY, STANDARDY, WAGI, ocena_standardu
from .kontekst import Kontekst, nazwa_motywu
from .pbi.model import Model
from .pbi.raport import CHROM, otworz

KOLEJ = {"blad": 0, "ostrzezenie": 1, "info": 2}


def czytaj_json(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def wybor(standardy=None, profil=None, wylaczone=None) -> tuple[list[str], set[str]]:
    """Lista wybranych standardów (w kolejności katalogu) i zbiór wyłączonych reguł."""
    if standardy:
        st = [s for s in STANDARDY if s in set(standardy)]
    elif profil and profil in PROFILE:
        st = [s for s in STANDARDY if s in set(PROFILE[profil]["standardy"])]
    else:
        st = [s for s in STANDARDY if s in set(DOMYSLNE)]
    return st, set(wylaczone or [])


def uruchom(ctx: Kontekst):
    problemy, status, bledy = [], {}, []
    for fn in FUNKCJE:
        rid = fn.regula_id
        try:
            wyn = list(fn(ctx) or [])
        except Exception:                           # reguła nie może zatrzymać całej kontroli
            bledy.append(f"{rid}: {traceback.format_exc(limit=3)}")
            status[rid] = "błąd reguły"
            continue
        problemy += wyn
        status[rid] = "ok" if not wyn else str(len(wyn))
    return problemy, status, bledy


def oceny(problemy: list[dict], standardy: list[str], wylaczone: set[str], status: dict) -> tuple[dict, int | None]:
    out = {}
    for sid in standardy:
        aktywne = {r for r in STANDARDY[sid].reguly if r not in wylaczone and status.get(r) != "błąd reguły"}
        if not aktywne:
            out[sid] = {"punkty": None, "liczniki": {"blad": 0, "ostrzezenie": 0, "info": 0}}
            continue
        out[sid] = ocena_standardu([p for p in problemy if p["standard"] == sid], aktywne)
    pkt = [o["punkty"] for o in out.values() if o["punkty"] is not None]
    return out, (round(sum(pkt) / len(pkt)) if pkt else None)


def strony(ctx: Kontekst, problemy: list[dict]) -> list[dict]:
    """Geometria stron dla panelu: wizualizacje z prostokątami i znaleziskami (panel filtruje wg wyboru)."""
    out = []
    oceniane = {s.nazwa for s in ctx.strony()}
    for s in ctx.raport.strony:
        if s.nazwa not in oceniane:
            continue
        per_wiz = {}
        for p in problemy:
            if p.get("id_strony") == s.nazwa and p.get("id_wizualizacji"):
                per_wiz.setdefault(p["id_wizualizacji"], []).append(
                    {"regula": p["regula"], "waga": p["waga"], "opis": p["opis"], "standard": p["standard"]})
        wiz = []
        for v in sorted(s.wizualizacje, key=lambda v: v.z):
            if v.typ == "group":
                continue
            wiz.append({"nazwa": v.nazwa, "typ": v.typ, "etykieta": v.etykieta, "x": v.x, "y": v.y, "w": v.w, "h": v.h,
                        "ukryta": v.ukryta, "chrom": v.typ in CHROM, "problemy": per_wiz.get(v.nazwa, [])})
        out.append({"nazwa": s.nazwa, "tytul": s.tytul, "w": s.w, "h": s.h, "ukryta": s.ukryta,
                    "obszar": list(ctx.obszar(s)), "wizualizacje": wiz,
                    "problemy_strony": [{"regula": p["regula"], "waga": p["waga"], "opis": p["opis"],
                                         "standard": p["standard"]} for p in problemy
                                        if p.get("id_strony") == s.nazwa and not p.get("id_wizualizacji")]})
    return out


def wynik(raport_sciezka: str, model_sciezka: str | None = None, desktop: dict | None = None, konf: dict | None = None,
          standardy=None, profil=None, wylaczone=None, zrodlo: str = "") -> dict:
    ostrzezenia = []
    raport = otworz(raport_sciezka)
    model = None
    if model_sciezka:
        try:
            model = Model(czytaj_json(Path(model_sciezka)))
            if not model.tabele:
                model = None
                ostrzezenia.append("Model w Power BI był pusty (plik jeszcze się wczytywał) — oś czasu rozpoznana z nazw pól.")
        except Exception as e:  # noqa: BLE001
            ostrzezenia.append(f"Nie udało się odczytać modelu: {e} — oś czasu rozpoznana z nazw pól.")
    if (desktop or {}).get("niezapisane"):
        ostrzezenia.append("Raport ma niezapisane zmiany w Power BI — sprawdzona jest wersja zapisana na dysku. "
                           "Zapisz (Ctrl+S) i sprawdź ponownie.")
    ctx = Kontekst(raport, model, konf or {})
    problemy_obj, status, bledy = uruchom(ctx)
    problemy = [dict(p.__dict__, waga=p.waga or REGULY[p.regula].waga, standard=REGULY[p.regula].standard)
                for p in problemy_obj]
    st, wyl = wybor(standardy, profil, wylaczone)
    oc, ogolna = oceny(problemy, st, wyl, status)
    pominiete = [s for s in ctx.raport.strony if s not in ctx.strony()]
    if pominiete:
        ostrzezenia.append("Pominięte strony podpowiedzi: " + ", ".join(s.tytul for s in pominiete) + ".")
    return {
        "wersja": 1,
        "raport": raport.nazwa,
        "sciezka": raport.sciezka,
        "format": raport.format,
        "zapisano": raport.zapisano.isoformat(timespec="seconds") if raport.zapisano else None,
        "sprawdzono": datetime.now().isoformat(timespec="seconds"),
        "zrodlo": zrodlo,
        "desktop": desktop or {},
        "motyw": nazwa_motywu(raport),
        "model": {"status": "ok" if model else "brak",
                  "tabele": len(model.tabele) if model else 0},
        "standardy": [{"id": s.id, "nazwa": s.nazwa, "krotko": s.krotko, "opis": s.opis, "zrodlo": s.zrodlo,
                       "reguly": s.reguly} for s in STANDARDY.values()],
        "profile": PROFILE,
        "domyslne": DOMYSLNE,
        "reguly": {r.id: dict(r.__dict__, status=status.get(r.id, "")) for r in REGULY.values()},
        "problemy": problemy,
        "wybor": {"standardy": st, "wylaczone": sorted(wyl)},
        "oceny": oc,
        "ocena_ogolna": ogolna,
        "strony": strony(ctx, problemy),
        "ostrzezenia": ostrzezenia,
        "bledy_regul": bledy,
    }


def markdown(w: dict, standardy=None, wylaczone=None) -> str:
    """Lista zadań (Markdown) — tylko wybrane standardy i aktywne reguły."""
    st = standardy if standardy is not None else w["wybor"]["standardy"]
    wyl = set(wylaczone if wylaczone is not None else w["wybor"]["wylaczone"])
    nazwy = {s["id"]: s["nazwa"] for s in w["standardy"]}
    oc, ogolna = oceny(w["problemy"], st, wyl, {r: x["status"] for r, x in w["reguly"].items()})
    lin = [f"# Standardy wizualizacji — „{w['raport']}” ({w['sprawdzono'].replace('T', ' ')[:16]})", "",
           f"Plik: `{w['sciezka']}`  ", f"Ocena (wybrane standardy): **{ogolna if ogolna is not None else '—'}/100**  ",
           "Standardy: " + ", ".join(f"{nazwy[s]} {oc[s]['punkty'] if oc[s]['punkty'] is not None else '—'}" for s in st), "",
           "Poprawki w Power BI Desktop albo w plikach PBIR (np. z pomocą asystenta AI); po zmianach zapisz raport i sprawdź ponownie.", ""]
    pogr = {}
    for p in w["problemy"]:
        if p["standard"] in st and p["regula"] not in wyl:
            pogr.setdefault(p["regula"], []).append(p)
    if not pogr:
        lin.append("Brak problemów w wybranych standardach.")
    for rid in sorted(pogr, key=lambda r: (min(KOLEJ[p["waga"]] for p in pogr[r]), r)):
        reg = w["reguly"][rid]
        lin.append(f"## {rid} · {reg['tytul']} ({len(pogr[rid])}) — {nazwy[reg['standard']]}")
        lin.append(f"Jak naprawić: {reg['jak']}")
        for p in pogr[rid][:40]:
            gdzie = " › ".join(x for x in (p["strona"], p["obiekt"]) if x)
            lin.append(f"- [{WAGI[p['waga']]}] {gdzie}: {p['opis']}")
        if len(pogr[rid]) > 40:
            lin.append(f"- … i {len(pogr[rid]) - 40} kolejnych (wynik.json)")
        lin.append("")
    return "\n".join(lin)
