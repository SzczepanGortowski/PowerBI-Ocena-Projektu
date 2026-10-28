"""Spójność raportu — te same rzeczy wyglądają tak samo na każdej stronie."""
from __future__ import annotations

import itertools

from .katalog import odm, pl, regula
from .reguly_percepcja import _rodzina

SPOJNOSC = "Zasada spójności (IBCS UNIFY; Few 2006)"


@regula("SPJ-01", "spojnosc", "ostrzezenie", "Fragmentatory w tym samym miejscu na każdej stronie",
        "Ten sam filtr w innym miejscu na każdej stronie każe go szukać od nowa i sugeruje, że to inny filtr.",
        "Wspólne fragmentatory w stałym miejscu nagłówka (te same x, y, rozmiar), najlepiej zsynchronizowane.",
        SPOJNOSC)
def spj01(ctx):
    pozycje = {}
    for s in ctx.strony():
        for v in ctx.fragmentatory(s):
            klucz = tuple(sorted(p.get("queryRef") or "?" for rola in v.projekcje for p in v.projekcje[rola]))
            if klucz:
                pozycje.setdefault(klucz, []).append((s.tytul, v.x, v.y, v.w, v.h))
    for k, lst in pozycje.items():
        if len(lst) < 2:
            continue
        rozrzut = max(max(abs(a[i] - b[i]) for i in range(1, 5)) for a, b in itertools.combinations(lst, 2))
        if rozrzut > ctx.prog("pozycja_tolerancja_px", 4):
            strony = sorted({x[0] for x in lst})
            yield ctx.problem_rap("SPJ-01", f"Rozrzut położenia {rozrzut:.0f} px na stronach: {', '.join(strony)}.",
                                  obiekt=", ".join(x.split(".")[-1] for x in k))


@regula("SPJ-02", "spojnosc", "ostrzezenie", "Jedna miara = jeden kolor w całym raporcie",
        "Gdy miara zmienia kolor między stronami, czytelnik musi za każdym razem od nowa czytać legendę.",
        "Jawna mapa miara → kolor dla całego raportu (Format → Kolory danych z tym samym kolorem).",
        SPOJNOSC)
def spj02(ctx):
    mapa = {}
    for s in ctx.strony():
        for w in ctx.dane(s):
            for m, c in ctx.kolory_miar(w).items():
                mapa.setdefault(m, {}).setdefault(c, set()).add(s.tytul)
    for m, kol in mapa.items():
        if len(kol) > 1:
            yield ctx.problem_rap("SPJ-02", "; ".join(f"{c} na: {', '.join(sorted(st))}" for c, st in kol.items()) + ".",
                                  obiekt=m.split(".")[-1])


@regula("SPJ-03", "spojnosc", "info", "Jeden rozmiar tytułów wizualizacji",
        "Tytuły w różnych rozmiarach sugerują różną wagę wizualizacji, której zwykle nie ma.",
        "Rozmiar tytułu w motywie (visualStyles.*.title.fontSize), bez nadpisań per wizualizacja.",
        SPOJNOSC)
def spj03(ctx):
    rozm = {}
    for s in ctx.strony():
        for w in ctx.dane(s):
            if w.klasa in ("wykres", "tabela"):
                for t in ctx.teksty(w):
                    if t["element"] == "tytuł":
                        rozm.setdefault(t["pt"], []).append(f"{s.tytul}/{w.nazwa}")
    if len(rozm) > 2:
        opis = ", ".join(f"{pl(k, 1).removesuffix(',0')} pt ×{len(v)}" for k, v in sorted(rozm.items()))
        yield ctx.problem_rap("SPJ-03", f"{len(rozm)} rozmiary tytułów: {opis}.", obiekt="tytuły wizualizacji",
                              waga="ostrzezenie" if len(rozm) > 3 else "")


@regula("SPJ-04", "spojnosc", "info", "Jednakowy rozmiar stron",
        "Strony o różnych proporcjach skaczą przy przełączaniu i inaczej skalują się na ekranie.",
        "Jeden rozmiar kanwy dla stron raportu (np. 1280×720); wyjątki: strony podpowiedzi.",
        SPOJNOSC)
def spj04(ctx):
    rozm = {}
    for s in ctx.strony():
        rozm.setdefault((s.w, s.h), []).append(s.tytul)
    if len(rozm) > 1:
        opis = "; ".join(f"{w:g}×{h:g}: {', '.join(t[:3])}{'…' if len(t) > 3 else ''}" for (w, h), t in rozm.items())
        yield ctx.problem_rap("SPJ-04", f"{len(rozm)} rozmiary stron — {opis}.", obiekt="strony")


@regula("SPJ-05", "spojnosc", "info", "Najwyżej 2 kroje pisma w raporcie",
        "Różne kroje na różnych stronach sprawiają wrażenie raportu sklejonego z kilku.",
        "Krój z motywu (textClasses) na wszystkich stronach; usuń nadpisania fontFamily.",
        SPOJNOSC)
def spj05(ctx):
    rodz = {}
    for s in ctx.strony():
        for w in ctx.tresc(s):
            for t in ctx.teksty(w):
                r = _rodzina(t["kroj"])
                if r:
                    rodz.setdefault(r, set()).add(s.tytul)
    if len(rodz) > 2:
        yield ctx.problem_rap("SPJ-05", f"{odm(len(rodz), 'krój', 'kroje', 'krojów')}: "
                              + "; ".join(f"{r} ({len(st)} str.)" for r, st in sorted(rodz.items())) + ".",
                              obiekt="kroje pisma")
