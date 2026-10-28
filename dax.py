"""Lekki tokenizer DAX — wystarczający do reguł stylu (bez pełnego parsera).

Komentarze i literały tekstowe są osobnymi tokenami, więc reguły nie łapią
słów kluczowych z komentarzy ani z tekstów (np. „/” w etykiecie „m/m”).
"""
from __future__ import annotations

import re

_TOKEN = re.compile(r"""
  (?P<kom>//[^\n]*|--[^\n]*|/\*.*?\*/)
| (?P<tekst>"(?:[^"]|"")*")
| (?P<tabela>'(?:[^']|'')*')
| (?P<kolumna>\[(?:[^\]]|\]\])*\])
| (?P<liczba>\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)
| (?P<ident>[A-Za-z_][A-Za-z0-9_.]*)
| (?P<op><>|<=|>=|&&|\|\||==|[-+*/^&=<>,(){}!;:])
| (?P<ws>\s+)
| (?P<inne>.)
""", re.S | re.X)


class T:
    __slots__ = ("typ", "v", "poz")

    def __init__(self, typ, v, poz):
        self.typ, self.v, self.poz = typ, v, poz

    def __repr__(self):
        return f"{self.typ}:{self.v}"


def tokeny(wyr: str | None, z_komentarzami=False) -> list[T]:
    out = []
    if not wyr:
        return out
    for m in _TOKEN.finditer(wyr):
        typ = m.lastgroup
        if typ == "ws" or (typ == "kom" and not z_komentarzami):
            continue
        out.append(T(typ, m.group(), m.start()))
    return out


def nazwa_kolumny(tok: T) -> str:
    return tok.v[1:-1].replace("]]", "]")


def nazwa_tabeli(tok: T) -> str:
    return tok.v[1:-1].replace("''", "'") if tok.typ == "tabela" else tok.v


def odwolania(toks: list[T]):
    """(tabela | None, nazwa, indeks) dla każdego [..] w wyrażeniu."""
    out = []
    for i, t in enumerate(toks):
        if t.typ != "kolumna":
            continue
        tab = None
        if i > 0 and toks[i - 1].typ in ("tabela", "ident"):
            poprz = toks[i - 1]
            # ident tuż przed [ (bez spacji) to nazwa tabeli: Sprzedaz[Kwota]
            if poprz.typ == "tabela" or poprz.poz + len(poprz.v) == t.poz:
                tab = nazwa_tabeli(poprz)
        out.append((tab, nazwa_kolumny(t), i))
    return out


def wywolania(toks: list[T]):
    """(NAZWA_FUNKCJI, indeks '(', indeks pasującego ')') dla każdego wywołania."""
    out = []
    stos = []
    for i, t in enumerate(toks):
        if t.v == "(":
            f = toks[i - 1].v.upper() if i > 0 and toks[i - 1].typ == "ident" else None
            stos.append((f, i))
        elif t.v == ")" and stos:
            f, start = stos.pop()
            if f:
                out.append((f, start, i))
    return out


def argumenty(toks: list[T], otw: int, zam: int) -> list[list[T]]:
    """Podział tokenów między nawiasami na argumenty (przecinki na poziomie 0)."""
    args, biez, gl = [], [], 0
    for t in toks[otw + 1:zam]:
        if t.v in ("(", "{"):
            gl += 1
        elif t.v in (")", "}"):
            gl -= 1
        if t.v == "," and gl == 0:
            args.append(biez)
            biez = []
        else:
            biez.append(t)
    if biez or args:
        args.append(biez)
    return args


def tekst(toks: list[T]) -> str:
    return " ".join(t.v for t in toks)


def funkcje(toks: list[T]) -> set[str]:
    return {f for f, _, _ in wywolania(toks)}


def ma_var(toks: list[T]) -> bool:
    return any(t.typ == "ident" and t.v.upper() == "VAR" for t in toks)


def dzielenia_bez_divide(toks: list[T]) -> list[str]:
    """Fragmenty z operatorem '/', których mianownik nie jest niezerową stałą."""
    out = []
    for i, t in enumerate(toks):
        if t.v != "/":
            continue
        nast = toks[i + 1] if i + 1 < len(toks) else None
        if nast is not None and nast.v == "-" and i + 2 < len(toks):
            nast = toks[i + 2]
        if nast is not None and nast.typ == "liczba":
            try:
                if float(nast.v) != 0:
                    continue
            except ValueError:
                pass
        lewy = toks[max(0, i - 2):i]
        prawy = toks[i + 1:i + 3]
        out.append(tekst(lewy + [t] + prawy))
    return out


def glebokosc_if(toks: list[T]) -> int:
    """Największe zagnieżdżenie IF w IF (liczone jako liczba IF na stosie)."""
    stos, maks = [], 0
    for i, t in enumerate(toks):
        if t.v == "(":
            f = toks[i - 1].v.upper() if i > 0 and toks[i - 1].typ == "ident" else None
            stos.append(f)
            maks = max(maks, sum(1 for x in stos if x == "IF"))
        elif t.v == ")" and stos:
            stos.pop()
    return maks


def powtorzone_wywolania(toks: list[T], min_tokenow=6) -> list[str]:
    """Identyczne wywołania funkcji (np. ten sam CALCULATE dwa razy) — kandydat na VAR."""
    licznik: dict[str, int] = {}
    for f, o, z in wywolania(toks):
        if z - o < min_tokenow:
            continue
        klucz = tekst(toks[o - 1:z + 1])
        licznik[klucz] = licznik.get(klucz, 0) + 1
    return [k for k, n in licznik.items() if n > 1]


_HEX_W_TEKSCIE = re.compile(r"(?:#|%23)([0-9A-Fa-f]{6})(?![0-9A-Fa-f])")


def kolory_w_tekstach(toks: list[T]) -> list[str]:
    out = []
    for t in toks:
        if t.typ == "tekst":
            out += ["#" + m.lower() for m in _HEX_W_TEKSCIE.findall(t.v)]
    return out


_DATA_TEKST = re.compile(r'^"(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[./-]\d{1,2}[./-]\d{4})"$')


def zakodowane_daty(toks: list[T]) -> list[str]:
    out = []
    for i, t in enumerate(toks):
        if t.typ == "ident" and t.v.upper() == "DATE" and i + 2 < len(toks) and toks[i + 1].v == "(" \
                and toks[i + 2].typ == "liczba" and 1900 <= float(toks[i + 2].v) <= 2100:
            out.append(tekst(toks[i:i + 8]).split(")")[0] + ")")
        elif t.typ == "tekst" and _DATA_TEKST.match(t.v):
            out.append(t.v)
        elif t.typ == "ident" and t.v.lower() == "dt" and i + 1 < len(toks) and toks[i + 1].typ == "tekst":
            out.append("dt" + toks[i + 1].v)
    return out
