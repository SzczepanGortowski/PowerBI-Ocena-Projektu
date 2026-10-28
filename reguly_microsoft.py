"""Dobre praktyki Power BI według wskazówek Microsoft (projekt i wydajność raportu)."""
from __future__ import annotations

from .katalog import odm, regula
from .pbi.raport import CHROM, ROLE_KATEGORII
from .reguly_wcag import DOMYSLNA_NAZWA_STRONY

MS = "Microsoft Learn: Power BI report design tips; Optimization guide for Power BI"
LEGACY = {"card": "cardVisual", "table": "tableEx", "matrix": "pivotTable", "multiRowCard": "cardVisual"}
WYCOFANE = {"map": "azureMap", "filledMap": "azureMap", "qnaVisual": "Copilot"}
ROLE_GEO = {"X", "Y", "Latitude", "Longitude"}


@regula("MS-01", "microsoft", "ostrzezenie", "Nazwy stron opisują treść",
        "Nazwa strony to etykieta zakładki i pozycja nawigacji w aplikacji — „Strona 1” nic nie mówi odbiorcy.",
        "Dwuklik na zakładce strony i nazwa mówiąca, co jest na stronie.",
        MS)
def ms01(ctx):
    for s in ctx.strony():
        if DOMYSLNA_NAZWA_STRONY.match(s.tytul.strip()):
            yield ctx.problem_str(s, "MS-01", f"Domyślna nazwa strony „{s.tytul}”.")


@regula("MS-02", "microsoft", "ostrzezenie", "Liczba wizualizacji a wydajność",
        "Każda wizualizacja wysyła własne zapytanie przy otwarciu strony; powyżej ~15 strona ładuje się wolno.",
        "Podziel stronę, użyj drillthrough i podpowiedzi, połącz karty w jedną kartę z wieloma wartościami.",
        MS)
def ms02(ctx):
    for s in ctx.strony():
        n = len([v for v in s.widoczne() if v.typ not in CHROM])
        if n > ctx.prog("wizualizacje_wydajnosc", 15):
            yield ctx.problem_str(s, "MS-02", odm(n, "wizualizacja", "wizualizacje", "wizualizacji")
                                  + " wykonujących zapytania.", waga="blad" if n > 25 else "")


@regula("MS-03", "microsoft", "info", "Wizualizacje niestandardowe",
        "Wizualizacja z AppSource zależy od licencji i aktualizacji dostawcy (np. „license expired” zamiast danych) "
        "i nie zawsze korzysta z motywu ani funkcji dostępności.",
        "Natywna wizualizacja Power BI albo potwierdzona licencja organizacyjna.",
        MS)
def ms03(ctx):
    for v in sorted({x for x in ctx.raport.wizualizacje_niestandardowe if x}):
        yield ctx.problem_rap("MS-03", f"Raport używa wizualizacji niestandardowej „{v}”.", obiekt=v)


@regula("MS-04", "microsoft", "info", "Ukryte wizualizacje",
        "Ukryte wizualizacje to martwy balast, chyba że przełączają je zakładki.",
        "Usuń je albo opisz, którą zakładką są odsłaniane.",
        MS)
def ms04(ctx):
    for s in ctx.strony():
        ukryte = [w for w in s.wizualizacje if w.ukryta and w.typ != "group"]
        if ukryte:
            dop = "" if ctx.raport.zakladki else " Raport nie ma zakładek, więc nic ich nie odsłania."
            yield ctx.problem_str(s, "MS-04", odm(len(ukryte), "ukryta wizualizacja", "ukryte wizualizacje",
                                                  "ukrytych wizualizacji") + "." + dop)


@regula("MS-05", "microsoft", "ostrzezenie", "Jawne miary zamiast agregacji kolumn",
        "Niejawna miara (Suma/Średnia kolumny) nie ma formatu, opisu ani kontroli logiki, a przy grupach "
        "obliczeniowych nie działa.",
        "Miara DAX w modelu (z formatem i opisem) zamiast kolumny przeciągniętej do wartości.",
        MS)
def ms05(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            if w.klasa == "filtr":
                continue
            niejawne = []
            for rola, lst in w.projekcje.items():
                if rola in ROLE_KATEGORII or (w.typ in ("azureMap", "map") and rola in ROLE_GEO):
                    continue
                for p in lst:
                    pole = p.get("pole") or {}
                    if pole.get("rodzaj") == "Aggregation":
                        niejawne.append(f"{pole.get('encja')}[{pole.get('nazwa')}]")
            if niejawne:
                yield ctx.problem_wiz(s, w, "MS-05", "Niejawna agregacja: " + ", ".join(niejawne) + ".")


@regula("MS-06", "microsoft", "ostrzezenie", "Strony z treścią",
        "Pusta strona w opublikowanym raporcie to zwykle pozostałość po pracy.",
        "Usuń stronę albo ją ukryj, jeśli to szkic.",
        MS)
def ms06(ctx):
    for s in ctx.strony():
        if not s.widoczne():
            yield ctx.problem_str(s, "MS-06", "Strona bez widocznych wizualizacji.", waga="info" if s.ukryta else "")


@regula("MS-07", "microsoft", "info", "Nowoczesne typy wizualizacji",
        "Starsze typy (karta, tabela, macierz) mają uboższe formatowanie i dostępność; mapy Bing są wycofywane.",
        "Karta → nowa karta (cardVisual), tabela → tableEx, macierz → pivotTable; mapy → Azure Maps.",
        MS + "; Bing Maps retirement")
def ms07(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            if w.typ in WYCOFANE:
                yield ctx.problem_wiz(s, w, "MS-07", f"„{w.typ}” jest wycofywany — zastąp: {WYCOFANE[w.typ]}.",
                                      waga="ostrzezenie")
            elif w.typ in LEGACY:
                yield ctx.problem_wiz(s, w, "MS-07", f"Starszy typ „{w.typ}” — nowszy odpowiednik: {LEGACY[w.typ]}.")
