"""Projekt dashboardu (Few) — strona ogarnięta jednym spojrzeniem."""
from __future__ import annotations

from . import kolor
from .katalog import odm, regula

FEW = "Few 2006: Information Dashboard Design"


@regula("FEW-01", "dashboard", "ostrzezenie", "Najwyżej 8 wizualizacji danych na stronie",
        "Pamięć robocza mieści kilka elementów naraz; strona z kilkunastoma wykresami i kartami wymaga "
        "przeszukiwania zamiast spojrzenia.",
        "Podziel stronę, przenieś szczegóły do drillthrough albo podpowiedzi, połącz karty w jedną kartę z wieloma "
        "wartościami.",
        FEW + "; Miller 1956, Cowan 2001")
def few01(ctx):
    ostrz, blad = ctx.prog("wizualizacje_max", 8), ctx.prog("wizualizacje_blad", 12)
    for s in ctx.strony():
        n = len(ctx.dane(s))
        if n > ostrz:
            yield ctx.problem_str(s, "FEW-01", odm(n, "wizualizacja", "wizualizacje", "wizualizacji")
                                  + f" danych (zalecane ≤ {ostrz}).", waga="blad" if n > blad else "")


@regula("FEW-02", "dashboard", "info", "Najwyżej 4 fragmentatory na stronie",
        "Każdy fragmentator to decyzja do podjęcia przed odczytem; ich rząd zabiera miejsce danym.",
        "Rzadko używane filtry przenieś do panelu filtrów; wspólne fragmentatory synchronizuj między stronami.",
        FEW)
def few02(ctx):
    for s in ctx.strony():
        n = len(ctx.fragmentatory(s))
        if n > 4:
            yield ctx.problem_str(s, "FEW-02", odm(n, "fragmentator", "fragmentatory", "fragmentatorów") + " na stronie.",
                                  waga="ostrzezenie" if n > 6 else "")


@regula("FEW-03", "dashboard", "ostrzezenie", "Bez mierników (gauge)",
        "Miernik zajmuje dużo miejsca, a pokazuje jedną liczbę i kąt, który trudno porównać z innymi.",
        "Karta z wartością i odchyleniem od celu albo wykres pociskowy (bullet).",
        FEW)
def few03(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            if w.typ == "gauge":
                yield ctx.problem_wiz(s, w, "FEW-03", "Miernik (gauge).")


@regula("FEW-04", "dashboard", "info", "Strona mieści się na jednym ekranie",
        "Dashboard ma być widoczny bez przewijania; to, co pod krawędzią ekranu, zwykle nie zostaje zauważone.",
        "Kanwa 16:9 (1280×720) albo podział na strony / drillthrough zamiast wysokiej strony.",
        FEW)
def few04(ctx):
    for s in ctx.strony():
        if s.w and s.h / s.w > 0.8:
            yield ctx.problem_str(s, "FEW-04", f"Kanwa {s.w:g}×{s.h:g} — wyższa niż ekran, wymaga przewijania.")


def _ma_kontekst(ctx, w) -> bool:
    if w.typ == "kpi":
        return True
    if w.typ == "cardVisual":
        for e in w.obiekty.get("referenceLabel", []) or []:
            v = ((e or {}).get("properties") or {}).get("value")
            if isinstance(v, dict) and "expr" in v and ("Measure" in v["expr"] or "Aggregation" in v["expr"]):
                return True
        return len(ctx.miary(w)) > 1
    if w.typ == "multiRowCard":
        return True
    return False


@regula("FEW-05", "dashboard", "info", "Liczby z kontekstem",
        "Sama liczba („12 145”) nie mówi, czy to dobrze — potrzebuje porównania: cel, rok poprzedni, trend.",
        "Karta z etykietą referencyjną (vs PY, vs cel) albo wizualizacja KPI z celem.",
        FEW)
def few05(ctx):
    for s in ctx.strony():
        for w in ctx.dane(s):
            if w.klasa == "karta" and w.typ in ("card", "cardVisual") and not _ma_kontekst(ctx, w) \
                    and not ctx.karta_tekstowa(w):
                yield ctx.problem_wiz(s, w, "FEW-05", "Karta bez porównania (cel, rok poprzedni, trend).")


@regula("FEW-06", "dashboard", "info", "Ograniczona liczba kolorów na stronie",
        "Kilka kolorów da się odróżnić i zapamiętać; powyżej 6–8 barw kolor przestaje coś znaczyć.",
        "Kolor tylko dla serii, które coś znaczą; reszta w szarości (strategia wyróżniania).",
        FEW + "; Healey 1996")
def few06(ctx):
    for s in ctx.strony():
        barwy = set()
        for w in ctx.dane(s):
            k = ctx.kolory_serii(w)
            if k and not k[1]:
                barwy |= {kolor.norm(c) for c in k[0]}
            barwy |= ctx.kolory_kategorii(w)
        chrom = {c for c in barwy if c and kolor.chroma(c) > 15}
        if len(chrom) > 8:
            yield ctx.problem_str(s, "FEW-06", f"{len(chrom)} barw serii na stronie: {', '.join(sorted(chrom)[:10])}.")
