"""Percepcja danych — skuteczność kanału kodowania, integralność skali, kolor i hierarchia pisma."""
from __future__ import annotations

import re

from . import kolor
from .katalog import liczba, pl, regula
from .kontekst import DLUGOSC
from .pbi.raport import rodzina_fontu

MPS = "Cleveland i McGill 1984; Heer i Bostock 2010; Mackinlay 1986"

# kanał percepcyjny: (ocena 0..1, nazwa kanału); 1,0 = pozycja na wspólnej skali
KANALY = {
    "pieChart": (0.5, "kąt i pole wycinka"), "donutChart": (0.5, "kąt i długość łuku"),
    "treemap": (0.5, "pole prostokąta"), "gauge": (0.5, "kąt łuku miernika"),
    "filledMap": (0.4, "nasycenie barwy na mapie"), "shapeMap": (0.4, "nasycenie barwy na mapie"),
    "ribbonChart": (0.6, "grubość wstęgi"), "stackedAreaChart": (0.7, "pole warstw bez wspólnej bazy"),
    "hundredPercentStackedAreaChart": (0.7, "udział warstw bez wspólnej bazy"),
    "hundredPercentStackedColumnChart": (0.7, "udział segmentów bez wspólnej bazy"),
    "hundredPercentStackedBarChart": (0.7, "udział segmentów bez wspólnej bazy"),
    "funnel": (0.8, "długość bez wspólnej bazy"), "waterfallChart": (0.85, "pozycja bez wspólnej bazy"),
}
SKUMULOWANE = {"columnChart", "barChart", "lineStackedColumnComboChart"}


def kanal(ctx, w):
    """(ocena, nazwa kanału) albo None, gdy wykres koduje pozycją na wspólnej skali albo nie dotyczy."""
    if w.typ in ("map", "azureMap"):
        if w.projekcje_roli("PathID") or not w.projekcje_roli("Size"):
            return None             # trasy i punkty: położenie geograficzne to kodowanie naturalne
        return 0.5, "pole bąbla na mapie"
    if w.typ in KANALY:
        return KANALY[w.typ]
    if w.typ in SKUMULOWANE and (w.ma_serie or ctx.liczba_miar(w) > 1):
        return 0.75, "długość segmentów bez wspólnej bazy (słupki skumulowane)"
    return None


@regula("PERC-01", "percepcja", "info", "Skuteczny kanał kodowania",
        "Pozycję i długość na wspólnej osi odczytujemy kilkukrotnie dokładniej niż kąt, pole czy nasycenie "
        "barwy — porównanie kategorii na kole albo w treemapie bywa mylące.",
        "Do porównania kategorii: posortowany wykres słupkowy. Do porównania segmentów: słupki grupowane albo "
        "małe wielokrotności zamiast stosu.",
        MPS)
def perc01(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            if w.klasa not in ("wykres", "karta"):
                continue
            k = kanal(ctx, w)
            if k and k[0] < 0.85:
                yield ctx.problem_wiz(s, w, "PERC-01", f"Koduje {k[1]} (skuteczność {pl(k[0], 2)} wobec 1,0 dla "
                                      "pozycji na wspólnej osi).", waga="ostrzezenie" if k[0] <= 0.5 else "")


@regula("PERC-02", "percepcja", "blad", "Słupki i pola od zera (lie factor)",
        "Długość słupka koduje wartość. Oś zaczynająca się powyżej zera zawyża różnice (lie factor > 1) — "
        "a przy ukrytej osi czytelnik nawet tego nie zobaczy.",
        "Oś wartości słupków, pól i kaskad od 0 (valueAxis.start puste albo 0). Gdy liczą się małe różnice — "
        "wykres liniowy albo słupki odchyleń.",
        "Tufte 1983 (lie factor); " + MPS)
def perc02(ctx):
    yield from _os_od_zera(ctx, "PERC-02")


def _os_od_zera(ctx, rid):
    for s in ctx.strony():
        for w in s.widoczne():
            if w.typ not in DLUGOSC:
                continue
            o = ctx.os_wartosci(w)
            st = o["start"]
            if isinstance(st, (int, float)) and not isinstance(st, bool) and st > 0:
                yield ctx.problem_wiz(s, w, rid, f"Oś wartości zaczyna się od {liczba(st)}"
                                      + ("" if o["pokazana"] else " i jest ukryta — czytelnik nie wie o przycięciu") + ".")
            if str(o["skala"]).lower() == "log":
                yield ctx.problem_wiz(s, w, rid, "Skala logarytmiczna przy kodowaniu długością.")


@regula("PERC-03", "percepcja", "ostrzezenie", "Bez drugiej osi wartości",
        "Dwie skale na jednym wykresie sugerują zależność, którą tworzy wybór zakresów osi; przecięcia linii "
        "nic nie znaczą.",
        "Dwa wykresy jeden pod drugim ze wspólną osią czasu albo jedna miara znormalizowana (indeks, %).",
        "Few 2008 (Dual-scaled axes); " + MPS)
def perc03(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            if w.klasa == "wykres" and ctx.os_wartosci(w)["druga"]:
                yield ctx.problem_wiz(s, w, "PERC-03", "Wykres ma drugą oś Y.")


@regula("PERC-04", "percepcja", "ostrzezenie", "Najwyżej 4 miary na wykresie",
        "Każda kolejna seria to kolor do zapamiętania i dopasowania do legendy; powyżej 4 serii porównanie "
        "zamienia się w szukanie.",
        "Podziel na dwa wykresy, przenieś szczegóły do tabeli albo zostaw w kolorze tylko serię wyróżnioną.",
        "Healey 1996; Few 2006")
def perc04(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            if w.klasa != "wykres" or w.ma_serie:
                continue
            n = ctx.liczba_miar(w)
            if n > 4:
                yield ctx.problem_wiz(s, w, "PERC-04", f"{n} miar na jednym wykresie.", waga="blad" if n > 6 else "")


@regula("PERC-05", "percepcja", "ostrzezenie", "Kolory serii łatwe do rozróżnienia",
        "Dwie serie w kolorach różniących się o mniej niż ΔE00 15 trudno rozróżnić na małych znacznikach i w legendzie.",
        "Kolory serii z różnych odcieni palety; unikaj par pomarańcz–czerwień i kolorów o tej samej jasności.",
        "Sharma 2005 (CIEDE2000); Szafir 2018 (różnica barw w wizualizacji)")
def perc05(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            k = ctx.kolory_serii(w)
            if not k or len(set(k[0])) < 2:
                continue
            m = kolor.min_delta_e(k[0])
            if m and m[0] < 15:
                dop = " (paleta motywu przy założonej liczbie kategorii)" if k[1] else ""
                yield ctx.problem_wiz(s, w, "PERC-05", f"{m[1]} i {m[2]} różnią się o ΔE00 = {pl(m[0])}{dop}.",
                                      waga="info" if k[1] or m[0] >= 10 else "")


@regula("PERC-06", "percepcja", "info", "Czytelna hierarchia pisma",
        "Rozmiary różniące się o mniej niż 15% wyglądają jak ten sam poziom — trzy prawie równe rozmiary "
        "(8/9/10 pt) wyglądają na przypadkowe, a zbyt wiele poziomów rozbija hierarchię.",
        "Skala 3–5 poziomów (np. 28 / 14 / 12 / 10 pt) w motywie; usuń pojedyncze nadpisania fontSize.",
        "Skale typograficzne (krok ≥ 1,15–1,2×)")
def perc06(ctx):
    for s in ctx.strony():
        rozm = sorted({round(t["pt"] * 2) / 2 for w in ctx.tresc(s) for t in ctx.teksty(w)})
        if len(rozm) < 2:
            continue
        poziomy = [[rozm[0]]]
        for r in rozm[1:]:
            if r / poziomy[-1][-1] < 1.15:
                poziomy[-1].append(r)
            else:
                poziomy.append([r])
        n, rozrzut = len(poziomy), max(len(p) for p in poziomy)
        if n > 6 or rozrzut >= 3:
            opis = " | ".join("/".join(f"{x:g}" for x in p) for p in poziomy)
            yield ctx.problem_str(s, "PERC-06", f"Poziomy pisma: {opis} pt — {n} poziomów, do {rozrzut} prawie "
                                  "równych rozmiarów w jednym.", waga="ostrzezenie" if n > 7 or rozrzut >= 4 else "")


@regula("PERC-07", "percepcja", "ostrzezenie", "Najwyżej 2 kroje pisma na stronie",
        "Każdy krój to inny „głos”; mieszanie krojów rozbija spójność i hierarchię strony.",
        "Jedna rodzina (np. Segoe UI) i jej odmiany; usuń nadpisania fontFamily w wizualizacjach.",
        "Zasady typografii użytkowej")
def perc07(ctx):
    for s in ctx.strony():
        rodz = sorted({_rodzina(t["kroj"]) for w in ctx.tresc(s) for t in ctx.teksty(w)} - {""})
        if len(rodz) > 2:
            yield ctx.problem_str(s, "PERC-07", f"{len(rodz)} kroje pisma: {', '.join(rodz)}.")


def _rodzina(k):
    k = rodzina_fontu(k) or ""
    return re.sub(r"\s+(Semibold|SemiBold|Bold|Light|Semilight|SemiLight|Black|Regular|Medium)$", "", k)


@regula("PERC-08", "percepcja", "ostrzezenie", "Ta sama miara w tym samym kolorze",
        "Gdy ta sama miara ma na dwóch wykresach strony różne kolory, czytelnik szuka różnicy, której nie ma.",
        "Jawna mapa miara → kolor (Format → Kolumny/Kolory danych) i ta sama kolejność serii.",
        "Zasada spójności kodowania (Munzner 2014)")
def perc08(ctx):
    for s in ctx.strony():
        mapa = {}
        for w in ctx.dane(s):
            for m, c in ctx.kolory_miar(w).items():
                mapa.setdefault(m, {}).setdefault(c, []).append(w.nazwa)
        for m, kol in mapa.items():
            if len(kol) > 1:
                yield ctx.problem_str(s, "PERC-08", f"„{m.split('.')[-1]}”: "
                                      + "; ".join(f"{c} w {', '.join(v)}" for c, v in kol.items()) + ".")
