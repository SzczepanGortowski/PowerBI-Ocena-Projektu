"""Katalog standardów wizualizacji, rejestr reguł, znaleziska i ocena punktowa.

Każda reguła należy do jednego standardu. Silnik zawsze sprawdza wszystkie reguły; wybór standardów
(i wyłączenie pojedynczych reguł) decyduje o tym, co widać w wyniku i co liczy się do oceny.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

WAGI = {"blad": "błąd", "ostrzezenie": "ostrzeżenie", "info": "info"}
PUNKTY = {"blad": 10, "ostrzezenie": 4, "info": 1}


@dataclass
class Standard:
    id: str
    nazwa: str
    krotko: str
    opis: str
    zrodlo: str
    reguly: list = field(default_factory=list)


STANDARDY: dict[str, Standard] = {}


def _standard(id, nazwa, krotko, opis, zrodlo):
    STANDARDY[id] = Standard(id, nazwa, krotko, opis, zrodlo)


_standard("wcag", "Dostępność (WCAG 2.2 AA)", "Dostępność",
          "Czy raport odczyta osoba słabowidząca, z zaburzeniami widzenia barw albo z czytnikiem ekranu: "
          "kontrast tekstu i grafiki, kolory rozróżnialne przy daltonizmie, tekst alternatywny, kolejność "
          "tabulacji, rozmiar pisma.",
          "W3C WCAG 2.2 (SC 1.1.1, 1.4.1, 1.4.3, 1.4.11, 2.4.3, 2.4.6); Microsoft: Design Power BI reports "
          "for accessibility")
_standard("percepcja", "Percepcja danych (Cleveland–McGill)", "Percepcja",
          "Czy wykres koduje liczby kanałem, który oko odczytuje dokładnie (pozycja i długość zamiast kąta "
          "i pola), czy skala nie przekłamuje, czy kolory serii da się rozróżnić i czy hierarchia pisma jest czytelna.",
          "Cleveland i McGill 1984; Heer i Bostock 2010; Tufte 1983 (lie factor); Szafir 2018 (ΔE00)")
_standard("ibcs", "IBCS — notacja raportów biznesowych", "IBCS",
          "International Business Communication Standards: czas w poziomie, struktura w pionie, właściwe "
          "typy wykresów, scenariusze (rok poprzedni jaśniej niż wykonanie), tytuł z komunikatem, "
          "kolor tylko z sensem, osie bez manipulacji.",
          "IBCS 1.2 (SAY, UNIFY, CONDENSE, CHECK, EXPRESS, SIMPLIFY, STRUCTURE)")
_standard("minimalizm", "Minimalizm danych (Tufte)", "Minimalizm",
          "Mniej „atramentu” poza danymi: bez ram i cieni, bez siatki i osi dublujących etykiety danych, "
          "bez legendy przy jednej serii, bez nadmiernej precyzji.",
          "Tufte 1983: The Visual Display of Quantitative Information (data-ink ratio, chartjunk)")
_standard("dashboard", "Projekt dashboardu (Few)", "Dashboard",
          "Strona ogarnięta jednym spojrzeniem: ograniczona liczba wizualizacji i fragmentatorów, bez mierników, "
          "liczby z kontekstem (cel, rok poprzedni), mieści się na jednym ekranie.",
          "Few 2006: Information Dashboard Design; Miller 1956, Cowan 2001 (pamięć robocza)")
_standard("uklad", "Układ i Gestalt", "Układ",
          "Porządek na stronie: nic poza kanwą i nic na sobie, wyrównane krawędzie, rytm odstępów, równowaga, "
          "wykorzystany obszar, KPI nad szczegółami.",
          "Zasady Gestalt (bliskość, wyrównanie); Ngo, Teo, Byrne 2003 (miary estetyki interfejsu)")
_standard("spojnosc", "Spójność raportu", "Spójność",
          "Te same rzeczy wyglądają tak samo na każdej stronie: położenie fragmentatorów, kolor miary, "
          "rozmiary tytułów, kroje pisma, rozmiar stron.",
          "Zasada spójności (IBCS UNIFY, Few 2006)")
_standard("microsoft", "Dobre praktyki Power BI (Microsoft)", "Microsoft",
          "Higiena raportu według wskazówek Microsoft: nazwy stron, liczba wizualizacji a wydajność, jawne miary, "
          "nowoczesne typy wizualizacji, wizualizacje niestandardowe, ukryte i puste elementy.",
          "Microsoft Learn: Power BI report design tips; Optimization guide for Power BI")

PROFILE = {
    "podstawowy": {"nazwa": "Podstawowy", "standardy": ["wcag", "percepcja", "uklad", "spojnosc", "dashboard"]},
    "ibcs": {"nazwa": "Raport zarządczy (IBCS)", "standardy": ["ibcs", "percepcja", "minimalizm", "spojnosc", "wcag"]},
    "dostepnosc": {"nazwa": "Dostępność", "standardy": ["wcag"]},
    "wszystkie": {"nazwa": "Wszystkie", "standardy": list(STANDARDY)},
}
DOMYSLNE = PROFILE["podstawowy"]["standardy"]


@dataclass
class Regula:
    id: str
    standard: str
    waga: str               # blad | ostrzezenie | info
    tytul: str
    dlaczego: str
    jak: str
    zrodlo: str = ""
    wymaga: str = "raport"  # raport | model — model poprawia trafność, reguła działa też bez niego


@dataclass
class Problem:
    regula: str
    opis: str
    strona: str = ""
    obiekt: str = ""
    typ_obiektu: str = ""   # wizualizacja | strona | raport
    waga: str = ""          # nadpisanie wagi reguły
    id_strony: str = ""
    id_wizualizacji: str = ""


REGULY: dict[str, Regula] = {}
FUNKCJE: list = []


def regula(id, standard, waga, tytul, dlaczego, jak, zrodlo="", wymaga="raport"):
    """Dekorator: funkcja (ctx) -> iterowalne Problem."""
    def deco(fn):
        REGULY[id] = Regula(id, standard, waga, tytul, dlaczego, jak, zrodlo, wymaga)
        STANDARDY[standard].reguly.append(id)
        fn.regula_id = id
        FUNKCJE.append(fn)
        return fn
    return deco


def odm(n: int, jeden: str, kilka: str, wiele: str) -> str:
    """Liczebnik z rzeczownikiem: 1 miara, 3 miary, 5 miar, 22 miary, 12 miar."""
    if n == 1:
        return f"1 {jeden}"
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return f"{n} {kilka}"
    return f"{n} {wiele}"


def pl(x: float, miejsca: int = 1) -> str:
    return f"{x:.{miejsca}f}".replace(".", ",")


def liczba(x: float) -> str:
    """250000000 -> '250 000 000'; 0.5 -> '0,5'."""
    if float(x).is_integer():
        return f"{int(x):,}".replace(",", "\u00a0")
    return f"{x:,.2f}".rstrip("0").rstrip(".").replace(",", "\u00a0").replace(".", ",")


def ocena_standardu(problemy: list[dict], reguly_aktywne: set[str]) -> dict:
    """Standard startuje od 100; każda naruszona reguła odejmuje punkty wagi × (1 + log2 liczby
    wystąpień), najwyżej 3× punkty wagi."""
    per = {}
    licz = {"blad": 0, "ostrzezenie": 0, "info": 0}
    for p in problemy:
        if p["regula"] not in reguly_aktywne:
            continue
        licz[p["waga"]] += 1
        per[(p["regula"], p["waga"])] = per.get((p["regula"], p["waga"]), 0) + 1
    kara = sum(min(PUNKTY[w] * (1 + math.log2(n)), 3 * PUNKTY[w]) for (_, w), n in per.items())
    return {"punkty": max(0, round(100 - kara)), "liczniki": licz}
