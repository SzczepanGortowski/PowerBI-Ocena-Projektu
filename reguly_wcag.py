"""Dostępność — WCAG 2.2 AA i zalecenia Microsoft dla raportów dostępnych."""
from __future__ import annotations

import re

from . import kolor
from .katalog import pl, regula

DOMYSLNA_NAZWA_STRONY = re.compile(r"^(strona|page|duplikat|duplicate of|kopia)\b.*\d*$", re.I)
DEKORACJE = {"shape", "basicShape", "image", "group"}


@regula("WCAG-01", "wcag", "ostrzezenie", "Kontrast tekstu (SC 1.4.3)",
        "Tekst o kontraście poniżej 4,5:1 (3:1 dla tekstu ≥ 18 pt albo ≥ 14 pt pogrubionego) jest trudny do "
        "odczytania dla osób słabowidzących, na rzutniku i na ekranie w słońcu.",
        "Przyciemnij tekst albo rozjaśnij tło — w motywie (textClasses, visualStyles), nie w każdej wizualizacji. "
        "Tekst na obrazie tła strony oceń na zrzucie.",
        "WCAG 2.2 SC 1.4.3 Contrast (Minimum)")
def wcag01(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            tlo = ctx.tlo(s, w)
            if tlo is None:
                continue
            slabe = {}
            for t in ctx.teksty(w):
                if not t["kolor"]:
                    continue
                k = kolor.kontrast(t["kolor"], tlo)
                wym = 3.0 if t["pt"] >= 18 or (t["pt"] >= 14 and t["pogrubiony"]) else 4.5
                if k < wym:
                    slabe[t["element"]] = (k, f"{t['element']} {t['kolor']} na {tlo} = {pl(k)}:1 (wymagane {pl(wym)}:1)")
            if slabe:
                mn = min(k for k, _ in slabe.values())
                opis = "; ".join(o for _, o in sorted(slabe.values())[:4])
                yield ctx.problem_wiz(s, w, "WCAG-01", f"Słaby kontrast: {opis}.", waga="blad" if mn < 3 else "")


@regula("WCAG-02", "wcag", "ostrzezenie", "Kontrast elementów graficznych (SC 1.4.11)",
        "Słupek, linia czy punkt o kontraście poniżej 3:1 względem tła zlewa się z tłem — trudno go zobaczyć "
        "i porównać z innymi.",
        "Ciemniejszy odcień serii albo obrys. Jasne wypełnienie dopuszczalne, gdy wartość podaje etykieta danych.",
        "WCAG 2.2 SC 1.4.11 Non-text Contrast")
def wcag02(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            k = ctx.kolory_serii(w)
            tlo = ctx.tlo(s, w)
            if not k or tlo is None:
                continue
            kolory, zalozone = k
            slabe = sorted((kolor.kontrast(c, tlo), c) for c in dict.fromkeys(kolory) if kolor.kontrast(c, tlo) < 3)
            if not slabe:
                continue
            opis = "; ".join(f"{c} = {pl(x)}:1" for x, c in slabe[:4])
            if zalozone:
                opis += " (kolory z palety motywu przy założonej liczbie kategorii)"
            etykiety = ctx.etykiety_danych(w)
            if etykiety:
                opis += " — wartości podają etykiety danych"
            yield ctx.problem_wiz(s, w, "WCAG-02", f"Kolory serii o kontraście < 3:1 względem tła {tlo}: {opis}.",
                                  waga="info" if zalozone or etykiety else "")


@regula("WCAG-03", "wcag", "ostrzezenie", "Kolory serii rozróżnialne przy daltonizmie (SC 1.4.1)",
        "Około 8% mężczyzn ma zaburzenia widzenia barw. Gdy dwie serie po symulacji protanopii, deuteranopii "
        "albo tritanopii różnią się o mniej niż ΔE00 10, kolor przestaje być nośnikiem informacji.",
        "Para niebieski–pomarańczowy zamiast czerwony–zielony; drugie kodowanie: etykieta przy serii, linia "
        "przerywana, znak ▲▼. Paletę motywu zmienia właściciel motywu.",
        "WCAG 2.2 SC 1.4.1 Use of Color; Machado, Oliveira, Fernandes 2009 (symulacja CVD)")
def wcag03(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            k = ctx.kolory_serii(w)
            if not k or len(set(k[0])) < 2:
                continue
            kolory, zalozone = k
            najg = None
            for typ in kolor.MACHADO:
                m = kolor.min_delta_e(kolory, typ)
                if m and (najg is None or m[0] < najg[0]):
                    najg = (m[0], m[1], m[2], typ)
            if najg and najg[0] < 10:
                d, a, b, typ = najg
                dop = " (kolory z palety motywu przy założonej liczbie kategorii — policz serie na wykresie)" if zalozone else ""
                yield ctx.problem_wiz(s, w, "WCAG-03",
                                      f"Przy {kolor.NAZWY_CVD[typ]} {a} i {b} różnią się o ΔE00 = {pl(d)} (próg 10){dop}.",
                                      waga="info" if zalozone else "")


@regula("WCAG-04", "wcag", "info", "Tekst alternatywny (SC 1.1.1)",
        "Czytnik ekranu odczytuje tekst alternatywny zamiast wykresu — bez niego wizualizacja jest dla niego pusta.",
        "Ogólne → Tekst alternatywny: jedno zdanie, co pokazuje wizualizacja (może być miarą DAX z wnioskiem).",
        "WCAG 2.2 SC 1.1.1 Non-text Content; Microsoft: alt text w raportach Power BI")
def wcag04(ctx):
    for s in ctx.strony():
        for w in ctx.dane(s):
            if not ctx.ma_alt_text(w) and not ctx.karta_tekstowa(w):
                yield ctx.problem_wiz(s, w, "WCAG-04", "Brak tekstu alternatywnego.")


@regula("WCAG-05", "wcag", "ostrzezenie", "Minimalny rozmiar tekstu",
        "Tekst poniżej 9 pt (12 px kanwy) na typowym ekranie ma ok. 12 px — granica czytelności; przy "
        "pomniejszeniu raportu albo na laptopie staje się nieczytelny.",
        "Etykiety osi, danych, tabel i fragmentatorów ≥ 9 pt. Brakuje miejsca → mniej kategorii albo większy "
        "kafelek, nie mniejszy font.",
        "Microsoft: Design Power BI reports for accessibility (rozmiar tekstu)")
def wcag05(ctx):
    prog = ctx.prog("tekst_min_pt", 9)
    for s in ctx.strony():
        for w in s.widoczne():
            if (w.klasa == "chrom" and w.typ != "textbox") or not ctx.w_obszarze(s, w):
                continue
            male = {}
            for t in ctx.teksty(w):
                if t["pt"] < prog:
                    male[t["element"]] = min(t["pt"], male.get(t["element"], 99))
            if male:
                mn = min(male.values())
                opis = ", ".join(f"{e} {pl(p, 1).removesuffix(',0')} pt" for e, p in sorted(male.items(), key=lambda x: x[1]))
                yield ctx.problem_wiz(s, w, "WCAG-05", f"Tekst poniżej {prog} pt: {opis}.",
                                      waga="info" if mn >= prog - 1 else "")


def _tab(w):
    poz = w.surowe.get("position") if isinstance(w.surowe, dict) else None
    if not isinstance(poz, dict):
        cfg = (w.surowe or {}).get("config") or {}
        poz = ((cfg.get("layouts") or [{}])[0] or {}).get("position") or {}
    v = poz.get("tabOrder")
    return v if isinstance(v, (int, float)) else None


@regula("WCAG-06", "wcag", "info", "Kolejność tabulacji (SC 2.4.3)",
        "Klawisz Tab i czytnik ekranu przechodzą po wizualizacjach w kolejności tabulacji. Gdy jest "
        "nieustawiona albo rozmija się z układem strony, użytkownik klawiatury skacze po stronie bez ładu.",
        "Widok → Okienko Wybór → Kolejność tabulacji: od lewej do prawej, z góry na dół; elementy dekoracyjne "
        "ukryj przed tabulacją.",
        "WCAG 2.2 SC 2.4.3 Focus Order; Microsoft: tab order w raportach Power BI")
def wcag06(ctx):
    for s in ctx.strony():
        el = [(w, _tab(w)) for w in s.widoczne() if w.typ not in DEKORACJE]
        el = [(w, t) for w, t in el if t is not None]
        if len(el) < 3:
            continue
        if len({t for _, t in el}) == 1:
            yield ctx.problem_str(s, "WCAG-06", f"Wszystkie {len(el)} elementy mają tę samą kolejność tabulacji "
                                  f"({el[0][1]:g}) — Tab przechodzi w kolejności tworzenia wizualizacji.")
            continue
        czytanie = sorted(el, key=lambda e: (round(e[0].y / 30), e[0].x))
        tab = [t for _, t in czytanie]
        par = len(tab) * (len(tab) - 1) / 2
        odwr = sum(1 for i in range(len(tab)) for j in range(i + 1, len(tab)) if tab[i] > tab[j])
        if par and odwr / par > 0.25:
            pierwsze = [w.etykieta for w, _ in sorted(el, key=lambda e: e[1])[:3]]
            yield ctx.problem_str(s, "WCAG-06", f"Kolejność tabulacji rozmija się z układem strony ({odwr / par:.0%} par "
                                  f"odwróconych); pierwsze w kolejności: {', '.join(pierwsze)}.")


@regula("WCAG-07", "wcag", "info", "Nazwy stron i tytuły wizualizacji (SC 2.4.6)",
        "Czytnik ekranu ogłasza nazwę strony i tytuł wizualizacji — „Strona 1” albo wykres bez tytułu nie mówi, co jest dalej.",
        "Nazwa strony i tytuł wizualizacji opisują treść (np. „Sprzedaż wg regionów, 2026”).",
        "WCAG 2.2 SC 2.4.6 Headings and Labels")
def wcag07(ctx):
    for s in ctx.strony():
        if DOMYSLNA_NAZWA_STRONY.match(s.tytul.strip()):
            yield ctx.problem_str(s, "WCAG-07", f"Domyślna nazwa strony „{s.tytul}”.")
        bez = [w for w in ctx.dane(s) if w.klasa in ("wykres", "tabela") and not ctx.tytul_widoczny(w)]
        for w in bez:
            yield ctx.problem_wiz(s, w, "WCAG-07", "Tytuł wizualizacji wyłączony.")

