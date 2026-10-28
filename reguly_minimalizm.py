"""Minimalizm danych (Tufte) — atrament poza danymi."""
from __future__ import annotations

from . import kolor
from .katalog import regula
from .kontekst import KARTEZJANSKIE, KATEGORIE_KOLOREM

TUFTE = "Tufte 1983: data-ink ratio, chartjunk"


@regula("TUF-01", "minimalizm", "info", "Bez ram i cieni wokół wizualizacji",
        "Ramka i cień to atrament, który nie niesie danych — przy kilku kafelkach strona robi się ciężka, "
        "a wzrok zatrzymuje się na krawędziach zamiast na liczbach.",
        "Wyłącz obramowanie i cień (Ogólne → Efekty); grupuj wizualizacje odstępem albo tłem strony.",
        TUFTE)
def tuf01(ctx):
    for s in ctx.strony():
        for w in ctx.dane(s):
            zbedne = []
            if ctx.wart(w, "dropShadow", "show", kontener=True, domyslna=False) is True:
                zbedne.append("cień")
            if ctx.wart(w, "border", "show", kontener=True, domyslna=False) is True:
                rama = ctx.wart(w, "border", "color", kontener=True)
                tlo = ctx.tlo(s, w)
                if not (isinstance(rama, str) and tlo and kolor.norm(rama) == kolor.norm(tlo)):
                    zbedne.append(f"obramowanie {rama}" if isinstance(rama, str) else "obramowanie")
            if zbedne:
                yield ctx.problem_wiz(s, w, "TUF-01", "Ozdobne: " + ", ".join(zbedne) + ".")


@regula("TUF-02", "minimalizm", "info", "Bez siatki przy etykietach danych",
        "Gdy wartości podają etykiety, linie siatki nie pomagają niczego odczytać — są szumem pod danymi.",
        "Wyłącz linie siatki (Oś Y → Linie siatki) albo etykiety, jeśli wykres ma służyć do odczytu z osi.",
        TUFTE)
def tuf02(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            if w.typ in KARTEZJANSKIE and ctx.etykiety_danych(w):
                o = ctx.os_wartosci(w)
                if o["pokazana"] and o["siatka"]:
                    yield ctx.problem_wiz(s, w, "TUF-02", "Linie siatki obok etykiet danych.")


@regula("TUF-03", "minimalizm", "info", "Oś wartości albo etykiety danych — nie oba",
        "Oś wartości i etykiety danych mówią to samo; jedno z nich wystarczy (zwykle etykiety).",
        "Przy etykietach danych wyłącz oś wartości — wartości czyta się z etykiet przy słupkach.",
        TUFTE)
def tuf03(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            if w.typ in KARTEZJANSKIE and ctx.etykiety_danych(w) and ctx.os_wartosci(w)["pokazana"]:
                yield ctx.problem_wiz(s, w, "TUF-03", "Oś wartości i etykiety danych naraz.")


@regula("TUF-04", "minimalizm", "info", "Legenda tylko przy kilku seriach",
        "Legenda jednej serii tylko powtarza tytuł i zabiera miejsce.",
        "Wyłącz legendę; nazwę serii podaj w tytule.",
        TUFTE)
def tuf04(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            if w.klasa != "wykres" or w.ma_serie or ctx.liczba_miar(w) > 1 or w.typ in KATEGORIE_KOLOREM:
                continue
            v, skad = ctx.efekt(w, "legend", "show")
            if v is True and skad != "domyślna":
                yield ctx.problem_wiz(s, w, "TUF-04", "Legenda przy jednej serii.")


@regula("TUF-05", "minimalizm", "info", "Bez nadmiernej precyzji etykiet",
        "Trzy i więcej miejsc po przecinku w etykietach to cyfry, których nikt nie porównuje — utrudniają odczyt.",
        "Precyzja 0–1 miejsca i jednostki wyświetlania (tys., mln) w etykietach danych.",
        TUFTE)
def tuf05(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            if w.klasa != "wykres":
                continue
            p = ctx.wart(w, "labels", "labelPrecision")
            if isinstance(p, (int, float)) and not isinstance(p, bool) and p >= 3 and ctx.etykiety_danych(w):
                yield ctx.problem_wiz(s, w, "TUF-05", f"Etykiety z {int(p)} miejscami po przecinku.")
