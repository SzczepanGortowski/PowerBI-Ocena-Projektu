"""IBCS — International Business Communication Standards 1.2 (reguły sprawdzalne z definicji raportu)."""
from __future__ import annotations

from . import kolor
from .katalog import regula
from .pbi.raport import opis_pola
from .kontekst import KARTEZJANSKIE, LINIE, PLAN, PY, SLUPKI_PIONOWE, SLUPKI_POZIOME
from .reguly_percepcja import _os_od_zera

IBCS = "IBCS 1.2"
NIEWLASCIWE = {"pieChart": "koło", "donutChart": "pierścień", "gauge": "miernik", "funnel": "lejek",
               "treemap": "treemapa", "ribbonChart": "wstęgowy", "filledMap": "kartogram",
               "shapeMap": "kartogram", "stackedAreaChart": "warstwowy skumulowany",
               "hundredPercentStackedAreaChart": "warstwowy 100%"}


@regula("IBCS-01", "ibcs", "ostrzezenie", "Właściwe typy wykresów (EXPRESS)",
        "IBCS zastępuje koła, pierścienie, mierniki, lejki i treemapy wykresami słupkowymi i liniowymi — "
        "te pierwsze kodują kątem i polem, więc nie pozwalają porównać wartości.",
        "Struktura → słupki poziome posortowane; udział → słupki 100% albo kaskada; wykonanie vs cel → słupki z "
        "odchyleniem.",
        IBCS + " EX 1 (Replace inappropriate chart types)")
def ibcs01(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            if w.typ in NIEWLASCIWE:
                yield ctx.problem_wiz(s, w, "IBCS-01", f"Wykres typu {NIEWLASCIWE[w.typ]} ({w.typ}).")


@regula("IBCS-02", "ibcs", "ostrzezenie", "Czas w poziomie, struktura w pionie (UNIFY)",
        "W notacji IBCS oś czasu biegnie poziomo (kolumny, linie), a kategorie strukturalne (regiony, produkty) "
        "pionowo (słupki poziome). Czas na słupkach poziomych albo w wierszach macierzy łamie tę konwencję.",
        "Okresy na wykresie kolumnowym albo liniowym; w macierzy okresy w kolumnach, struktura w wierszach.",
        IBCS + " UN 3 (Unify dimensions: time horizontal, structure vertical)", wymaga="model")
def ibcs02(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            kat = ctx.kategorie(w)
            if w.typ in SLUPKI_POZIOME and kat and ctx.czy_czas(kat[0]):
                yield ctx.problem_wiz(s, w, "IBCS-02", f"Czas („{(kat[0].get('pole') or {}).get('nazwa')}”) na osi pionowej "
                                      "wykresu słupkowego poziomego.")
            elif w.typ in ("pivotTable", "matrix"):
                wiersze, kolumny = w.projekcje_roli("Rows"), w.projekcje_roli("Columns")
                if wiersze and kolumny and ctx.czy_czas(wiersze[0]) and not any(ctx.czy_czas(k) for k in kolumny):
                    yield ctx.problem_wiz(s, w, "IBCS-02", "Okresy w wierszach, struktura w kolumnach macierzy.",
                                          waga="info")


@regula("IBCS-03", "ibcs", "ostrzezenie", "Linia tylko dla czasu i wartości ciągłych (EXPRESS)",
        "Linia łączy punkty, więc sugeruje przebieg między nimi. Między regionami czy produktami nie ma „przebiegu” — "
        "linia na kategoriach nominalnych wprowadza w błąd.",
        "Kategorie nominalne pokaż na słupkach; linię zostaw dla okresów i skal liczbowych.",
        IBCS + " EX 2 (Use line charts for time series)", wymaga="model")
def ibcs03(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            kat = ctx.kategorie(w)
            if w.typ in LINIE and kat and not ctx.czy_czas(kat[0]) and not ctx.czy_ciagla(kat[0])                     and not ctx.czy_porzadkowa(kat[0]):
                nazwa = (kat[0].get("pole") or {}).get("nazwa") or kat[0].get("queryRef")
                yield ctx.problem_wiz(s, w, "IBCS-03", f"Linia na kategoriach „{nazwa}”, które nie wyglądają na czas "
                                      "ani skalę liczbową.", waga="" if ctx.model else "info")


@regula("IBCS-04", "ibcs", "ostrzezenie", "Scenariusze: rok poprzedni jaśniej niż wykonanie (UNIFY)",
        "IBCS koduje scenariusze wyglądem: wykonanie (AC) ciemnoszare, rok poprzedni (PY) jasnoszare, plan (PL) "
        "kontur. Kolorowy albo ciemniejszy PY odwraca hierarchię i myli się z wykonaniem.",
        "PY w jasnej szarości (np. #bfbfbf), AC ciemne; plan jako linia przerywana albo obrys.",
        IBCS + " UN 1 (Unify scenarios)")
def ibcs04(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            mapa = ctx.kolory_miar(w)
            if len(mapa) < 2:
                continue
            ac = {m: c for m, c in mapa.items() if not PY.search(m) and not PLAN.search(m)}
            py = {m: c for m, c in mapa.items() if PY.search(m)}
            if not ac or not py:
                continue
            l_ac = max(kolor.lab(c)[0] for c in ac.values())
            for m, c in py.items():
                l_py, chr_py = kolor.lab(c)[0], kolor.chroma(c)
                if chr_py > 20 or l_py <= l_ac + 5:
                    powod = "kolorowy" if chr_py > 20 else "nie jaśniejszy niż wykonanie"
                    yield ctx.problem_wiz(s, w, "IBCS-04", f"„{m.split('.')[-1]}” ({c}) — {powod}.")


@regula("IBCS-05", "ibcs", "info", "Bez zbędnych elementów (SIMPLIFY)",
        "Oś wartości obok etykiet danych, linie siatki i cienie powtarzają informację albo jej nie niosą — "
        "odciągają wzrok od liczb.",
        "Przy etykietach danych wyłącz oś wartości i siatkę; usuń cienie i ozdobne ramki.",
        IBCS + " SI 1–3 (Avoid cluttered layout, redundancy, decoration)")
def ibcs05(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            if w.klasa != "wykres":
                continue
            o = ctx.os_wartosci(w)
            zbedne = []
            if w.typ in KARTEZJANSKIE and ctx.etykiety_danych(w) and o["pokazana"]:
                zbedne.append("oś wartości obok etykiet danych")
                if o["siatka"]:
                    zbedne.append("linie siatki obok etykiet danych")
            if ctx.wart(w, "dropShadow", "show", kontener=True, domyslna=False) is True:
                zbedne.append("cień")
            if zbedne:
                yield ctx.problem_wiz(s, w, "IBCS-05", "Zbędne: " + ", ".join(zbedne) + ".")


@regula("IBCS-06", "ibcs", "info", "Tytuł z komunikatem (SAY)",
        "IBCS zaczyna od przekazu: tytuł mówi, co z danych wynika. Tytuł automatyczny („Suma X wg Y”) albo jego "
        "brak zostawia wniosek czytelnikowi.",
        "Tytuł = wniosek albo pytanie (np. „Sprzedaż rośnie w regionach wschodnich”); miara, okres i jednostka w podtytule.",
        IBCS + " SA 1 (Know objectives), SA 3 (Deliver message)")
def ibcs06(ctx):
    for s in ctx.strony():
        for w in ctx.dane(s):
            if w.klasa not in ("wykres", "tabela"):
                continue
            if not ctx.tytul_widoczny(w):
                yield ctx.problem_wiz(s, w, "IBCS-06", "Brak tytułu.", waga="ostrzezenie")
            elif not (isinstance(w.tytul_tekst, str) and w.tytul_tekst.strip()):
                yield ctx.problem_wiz(s, w, "IBCS-06", "Tytuł automatyczny z nazw pól.")


@regula("IBCS-07", "ibcs", "blad", "Skala bez manipulacji (CHECK)",
        "Przycięta oś słupków albo skala logarytmiczna przy kodowaniu długością przekłamuje proporcje.",
        "Oś wartości słupków od zera; małe różnice pokaż wykresem odchyleń.",
        IBCS + " CH 1 (Avoid manipulated axes)")
def ibcs07(ctx):
    yield from _os_od_zera(ctx, "IBCS-07")


@regula("IBCS-08", "ibcs", "ostrzezenie", "Kolor tylko z sensem (EXPRESS)",
        "Pokolorowanie kategorii jednej serii na różne barwy nic nie znaczy, a sugeruje różnice. IBCS używa koloru "
        "do wyróżnienia i oceny (dobrze/źle), nie do dekoracji.",
        "Jedna barwa dla serii; kolorem wyróżnij tylko element, o którym mówi tytuł.",
        IBCS + " EX 4 (Use colors only for highlighting and signals)")
def ibcs08(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            if w.klasa != "wykres" or w.ma_serie or ctx.liczba_miar(w) > 1:
                continue
            k = ctx.kolory_kategorii(w)
            if len(k) >= 3:
                yield ctx.problem_wiz(s, w, "IBCS-08", f"{len(k)} różne kolory kategorii w jednej serii.")


def _sortowanie(w):
    sd = (((w.surowe or {}).get("visual") or {}).get("query") or {}).get("sortDefinition") or {}
    s = (sd.get("sort") or [None])[0]
    if not isinstance(s, dict):
        return None
    return opis_pola(s.get("field")), s.get("direction")


@regula("IBCS-09", "ibcs", "info", "Kategorie strukturalne posortowane wg wartości (STRUCTURE)",
        "Słupki regionów czy produktów ułożone alfabetycznie każą szukać największych; posortowane wg wartości "
        "pokazują ranking od razu.",
        "Sortuj malejąco po mierze (Więcej opcji → Sortuj według). Kolejność alfabetyczną zostaw dla list do wyszukiwania.",
        IBCS + " ST 3 (Use appropriate order)")
def ibcs09(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            if w.typ not in SLUPKI_POZIOME | SLUPKI_PIONOWE:
                continue
            kat = ctx.kategorie(w)
            so = _sortowanie(w)
            if not kat or not so or ctx.czy_czas(kat[0]) or ctx.czy_ciagla(kat[0]) or ctx.czy_porzadkowa(kat[0]):
                continue
            pole, kier = so
            k = kat[0].get("pole") or {}
            if pole.get("rodzaj") == "Column" and (pole.get("encja"), pole.get("nazwa")) == (k.get("encja"), k.get("nazwa")):
                yield ctx.problem_wiz(s, w, "IBCS-09", f"Sortowanie po nazwie kategorii „{k.get('nazwa')}” "
                                      f"({'rosnąco' if kier == 'Ascending' else 'malejąco'}), nie po wartości.")


@regula("IBCS-10", "ibcs", "ostrzezenie", "Jednolita skala dla tej samej miary (UNIFY)",
        "Ta sama miara na dwóch wykresach strony z różnie ustawionym zakresem osi wygląda porównywalnie, "
        "a nie jest — równe słupki znaczą różne liczby.",
        "Ten sam zakres osi (start/koniec) dla tej samej miary albo wskaźnik skali przy wykresach.",
        IBCS + " UN 4 (Unify scaling)")
def ibcs10(ctx):
    for s in ctx.strony():
        zakresy = {}
        for w in s.widoczne():
            if w.klasa != "wykres":
                continue
            o = ctx.os_wartosci(w)
            if o["start"] is None and o["koniec"] is None:
                continue
            for m in ctx.miary(w):
                zakresy.setdefault(m, {}).setdefault((o["start"], o["koniec"]), []).append(w.nazwa)
        for m, z in zakresy.items():
            if len(z) > 1:
                opis = "; ".join(f"{a if a is not None else 'auto'}–{b if b is not None else 'auto'} w {', '.join(v)}"
                                 for (a, b), v in z.items())
                yield ctx.problem_str(s, "IBCS-10", f"„{m.split('.')[-1]}” z różnymi zakresami osi: {opis}.")
