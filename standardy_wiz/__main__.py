"""Standardy wizualizacji — kontrola raportu Power BI według wybranych standardów (tylko odczyt).

Użycie (zwykle wywołuje to panel w Power BI Desktop przez analiza.ps1):
  python standardy.py --raport "<.pbip | .pbix | folder .Report>" [--model model.json]
                      [--standardy wcag,ibcs | --profil podstawowy|ibcs|dostepnosc|wszystkie]
                      [--wylaczone IBCS-05,TUF-02] [--wyjscie folder]
  python standardy.py --lista            # standardy, profile i reguły
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

from .katalog import PROFILE, REGULY, STANDARDY, WAGI
from .silnik import czytaj_json, markdown, wynik

NARZEDZIE = Path(__file__).resolve().parent.parent


def _lista():
    print("Profile:")
    for k, p in PROFILE.items():
        print(f"  {k:<12} {p['nazwa']}: {', '.join(p['standardy'])}")
    for s in STANDARDY.values():
        print(f"\n{s.id} — {s.nazwa}\n  {s.opis}\n  Źródło: {s.zrodlo}")
        for rid in s.reguly:
            r = REGULY[rid]
            print(f"  {rid:<8} [{WAGI[r.waga]}] {r.tytul}")


def _bezpieczna(s: str) -> str:
    return "".join(c if c.isalnum() or c in " ._-" else "_" for c in s).strip() or "raport"


def glowna(argv=None):
    ap = argparse.ArgumentParser(description="Kontrola raportu Power BI według wybranych standardów wizualizacji")
    ap.add_argument("--raport", help=".pbip, .pbix albo folder *.Report")
    ap.add_argument("--model", help="TMSL modelu (opcjonalnie — lepsze rozpoznanie osi czasu)")
    ap.add_argument("--standardy", help="identyfikatory standardów po przecinku")
    ap.add_argument("--profil", choices=list(PROFILE), help="gotowy zestaw standardów")
    ap.add_argument("--wylaczone", help="identyfikatory reguł do pominięcia, po przecinku")
    ap.add_argument("--wybor", help="plik JSON {standardy: [...], wylaczone: [...]} (zapisuje go panel)")
    ap.add_argument("--wyjscie", help="folder wyników (domyślnie %%TEMP%%/StandardyWizualizacji/<raport>)")
    ap.add_argument("--desktop", help="stan Desktopa z analiza.ps1 (json: plik, niezapisane)")
    ap.add_argument("--zrodlo", default="", help="opis instancji Desktopa (do nagłówka)")
    ap.add_argument("--konfiguracja", help="plik progów (domyślnie konfiguracja.json obok)")
    ap.add_argument("--lista", action="store_true", help="wypisz standardy, profile i reguły")
    a = ap.parse_args(argv)

    if a.lista:
        _lista()
        return 0
    if not a.raport:
        ap.error("podaj --raport albo --lista")

    konf_p = Path(a.konfiguracja) if a.konfiguracja else NARZEDZIE / "konfiguracja.json"
    konf = {k: v for k, v in czytaj_json(konf_p).items() if not k.startswith("$")} if konf_p.exists() else {}
    standardy = [x.strip() for x in a.standardy.split(",") if x.strip()] if a.standardy else None
    wylaczone = [x.strip() for x in a.wylaczone.split(",") if x.strip()] if a.wylaczone else None
    if a.wybor and Path(a.wybor).exists():
        wyb = czytaj_json(Path(a.wybor))
        standardy = standardy or wyb.get("standardy")
        wylaczone = wylaczone or wyb.get("wylaczone")
    desktop = czytaj_json(Path(a.desktop)) if a.desktop and Path(a.desktop).exists() else None

    try:
        w = wynik(a.raport, a.model, desktop, konf, standardy, a.profil, wylaczone, a.zrodlo)
    except Exception as e:  # noqa: BLE001
        print(f"BŁĄD: nie udało się sprawdzić raportu: {e}", file=sys.stderr)
        return 2

    out = Path(a.wyjscie) if a.wyjscie else Path(tempfile.gettempdir()) / "StandardyWizualizacji" / _bezpieczna(w["raport"])
    out.mkdir(parents=True, exist_ok=True)
    w["folder"] = str(out)
    (out / "wynik.json").write_text(json.dumps(w, ensure_ascii=False, indent=1), encoding="utf-8")
    md = markdown(w)
    (out / "zadania.md").write_text(md, encoding="utf-8")

    nazwy = {s["id"]: s["nazwa"] for s in w["standardy"]}
    print(f"Raport: {w['raport']} ({w['format']}) · motyw: {w['motyw']} · model: {w['model']['status']}")
    print(f"Ocena (wybrane standardy): {w['ocena_ogolna'] if w['ocena_ogolna'] is not None else '—'}/100")
    for sid, o in w["oceny"].items():
        l = o["liczniki"]
        print(f"  {nazwy[sid]}: {o['punkty'] if o['punkty'] is not None else '—'}/100 "
              f"(błędy {l['blad']}, ostrzeżenia {l['ostrzezenie']}, info {l['info']})")
    for o in w["ostrzezenia"]:
        print("  ! " + o)
    for b in w["bledy_regul"]:
        print("  ! błąd reguły " + b.splitlines()[0])
    print(f"WYNIK: {out / 'wynik.json'}")
    return 0


if __name__ == "__main__":
    if os.name == "nt":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(glowna())
