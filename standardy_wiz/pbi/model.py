"""Model semantyczny z TMSL (TOM JsonSerializer) + stany obiektów + wyniki zapytań DAX."""
from __future__ import annotations

import html
import re

from . import dax

AUTO_DATA = ("LocalDateTable_", "DateTableTemplate_")


def _tekst(v) -> str:
    if isinstance(v, list):
        return "\n".join(str(x) for x in v)
    return v or ""


class Kolumna:
    def __init__(self, tabela, d):
        self.tabela = tabela
        self.nazwa = d.get("name", "")
        self.typ = d.get("type", "data")              # data | calculated | calculatedTableColumn | rowNumber
        self.typ_danych = d.get("dataType", "")
        self.ukryta = bool(d.get("isHidden"))
        self.opis = _tekst(d.get("description"))
        self.format = d.get("formatString")
        self.kategoria = d.get("dataCategory")
        self.klucz = bool(d.get("isKey"))
        self.wyrazenie = _tekst(d.get("expression"))
        self.sortuj_wg = d.get("sortByColumn")
        self.sumuj = d.get("summarizeBy")


class Miara:
    def __init__(self, tabela, d):
        self.tabela = tabela
        self.nazwa = d.get("name", "")
        self.wyrazenie = _tekst(d.get("expression"))
        self.format = d.get("formatString")
        self.format_dynamiczny = bool(d.get("formatStringDefinition"))
        self.folder = d.get("displayFolder") or ""
        self.opis = _tekst(d.get("description"))
        self.ukryta = bool(d.get("isHidden"))
        self.stan = "Ready"
        self.blad = ""
        self.test = None                               # wynik zapytania DAX (dict) albo None
        self._toks = None

    @property
    def toks(self):
        if self._toks is None:
            self._toks = dax.tokeny(self.wyrazenie)
        return self._toks

    @property
    def pelna(self):
        return f"'{self.tabela}'[{self.nazwa}]"


class Tabela:
    def __init__(self, d):
        self.nazwa = d.get("name", "")
        self.ukryta = bool(d.get("isHidden"))
        self.opis = _tekst(d.get("description"))
        self.kategoria = d.get("dataCategory")
        self.kolumny = [Kolumna(self.nazwa, c) for c in d.get("columns", []) or [] if c.get("type") != "rowNumber"]
        self.miary = [Miara(self.nazwa, m) for m in d.get("measures", []) or []]
        self.partycje = d.get("partitions", []) or []
        self.hierarchie = d.get("hierarchies", []) or []
        self.grupa_obliczeniowa = d.get("calculationGroup")
        self.auto_data = self.nazwa.startswith(AUTO_DATA)
        zr = [(p.get("source") or {}) for p in self.partycje]
        self.obliczeniowa = any(s.get("type") == "calculated" for s in zr)
        self.wyrazenie = "\n".join(_tekst(s.get("expression")) for s in zr if s.get("type") == "calculated")
        self.tryby = {p.get("mode", "import") for p in self.partycje}

    @property
    def kolumny_danych(self):
        return [c for c in self.kolumny if c.typ in ("data", "calculatedTableColumn") or c.typ is None]

    @property
    def tabela_miar(self) -> bool:
        """Pusty kontener na miary: brak widocznych kolumn danych (dopuszczalna jedna ukryta pomocnicza)."""
        if not self.miary or self.grupa_obliczeniowa:
            return False
        widoczne = [c for c in self.kolumny if not c.ukryta]
        return not widoczne and len(self.kolumny) <= 1


class Model:
    def __init__(self, tmsl: dict, stany: dict | None = None, testy: dict | None = None):
        self.surowy = tmsl
        m = tmsl.get("model", {}) or {}
        self.nazwa_bazy = tmsl.get("name", "")
        self.poziom_zgodnosci = tmsl.get("compatibilityLevel")
        self.tabele = [Tabela(t) for t in m.get("tables", []) or []]
        self.relacje = [_relacja(r) for r in m.get("relationships", []) or []]
        self.role = m.get("roles", []) or []
        self.perspektywy = m.get("perspectives", []) or []
        self.zrodla = m.get("dataSources", []) or []
        self.adnotacje = {a.get("name"): a.get("value") for a in m.get("annotations", []) or []}
        self.zniechecaj_niejawne = bool(m.get("discourageImplicitMeasures"))
        self._t = {t.nazwa.casefold(): t for t in self.tabele}
        self._m = {}
        for t in self.tabele:
            for x in t.miary:
                self._m.setdefault(x.nazwa.casefold(), x)
        self._k = {}
        for t in self.tabele:
            for c in t.kolumny:
                self._k.setdefault(c.nazwa.casefold(), []).append(c)
        self._wczytaj_stany(stany or {})
        self.testy = testy or {}
        self.liczby_wierszy = {}
        for w in (self.testy.get("wiersze") or []):
            if isinstance(w.get("n"), (int, float)):
                self.liczby_wierszy[w["tabela"]] = int(w["n"])
        for wyn in self.testy.get("miary") or []:
            mi = self.miara(wyn.get("miara"))
            if mi is not None and mi.tabela == wyn.get("tabela"):
                mi.test = wyn
        self.zaleznosci = _zaleznosci_dmv(self.testy.get("zaleznosci_xml"))
        self.licznosci = {}
        for w in _zaleznosci_dmv(self.testy.get("statystyki_xml")) or []:
            w = {k.strip("[]"): v for k, v in w.items()}
            try:
                self.licznosci[(w["Table Name"].casefold(), w["Column Name"].casefold())] = int(float(w["Cardinality"]))
            except (KeyError, ValueError):
                pass

    # ------------------------------------------------------------ dostęp
    def tabela(self, nazwa) -> Tabela | None:
        return self._t.get((nazwa or "").casefold())

    def miara(self, nazwa) -> Miara | None:
        return self._m.get((nazwa or "").casefold())

    def kolumna(self, tabela, nazwa) -> Kolumna | None:
        t = self.tabela(tabela)
        if not t:
            return None
        for c in t.kolumny:
            if c.nazwa.casefold() == (nazwa or "").casefold():
                return c
        return None

    def kolumny_o_nazwie(self, nazwa) -> list[Kolumna]:
        return self._k.get((nazwa or "").casefold(), [])

    def miary_wszystkie(self):
        for t in self.tabele:
            yield from t.miary

    def kolumny_wszystkie(self):
        for t in self.tabele:
            yield from t.kolumny

    def wyrazenia(self):
        """(rodzaj, tabela, obiekt, wyrażenie) dla wszystkiego, co niesie DAX."""
        for t in self.tabele:
            for m in t.miary:
                yield "miara", t.nazwa, m.nazwa, m.wyrazenie
            for c in t.kolumny:
                if c.typ == "calculated":
                    yield "kolumna", t.nazwa, c.nazwa, c.wyrazenie
            if t.obliczeniowa:
                yield "tabela", t.nazwa, t.nazwa, t.wyrazenie
            for it in (t.grupa_obliczeniowa or {}).get("calculationItems", []) or []:
                yield "element", t.nazwa, it.get("name", ""), _tekst(it.get("expression"))
        for r in self.role:
            for tp in r.get("tablePermissions", []) or []:
                yield "rola", tp.get("name", ""), r.get("name", ""), _tekst(tp.get("filterExpression"))

    @property
    def auto_data_wlaczona(self):
        return any(t.auto_data for t in self.tabele) or self.adnotacje.get("__PBI_TimeIntelligenceEnabled") == "1"

    def _wczytaj_stany(self, stany):
        for s in stany.get("miary", []) or []:
            t = self.tabela(s.get("tabela"))
            if not t:
                continue
            for m in t.miary:
                if m.nazwa == s.get("nazwa"):
                    m.stan = s.get("stan") or "Ready"
                    m.blad = s.get("blad") or ""
        self.stany_kolumn = stany.get("kolumny", []) or []
        self.stany_partycji = stany.get("partycje", []) or []


def _relacja(r: dict) -> dict:
    return {
        "nazwa": r.get("name", ""),
        "z_tabeli": r.get("fromTable"), "z_kolumny": r.get("fromColumn"),
        "do_tabeli": r.get("toTable"), "do_kolumny": r.get("toColumn"),
        "aktywna": r.get("isActive", True),
        "kierunek": r.get("crossFilteringBehavior", "oneDirection"),
        "z_kard": r.get("fromCardinality", "many"), "do_kard": r.get("toCardinality", "one"),
        "opis": f"'{r.get('fromTable')}'[{r.get('fromColumn')}] → '{r.get('toTable')}'[{r.get('toColumn')}]",
    }


_DEK = re.compile(r"_x([0-9A-Fa-f]{4})_")


def _zaleznosci_dmv(xml: str | None) -> list[dict] | None:
    """Wiersze DISCOVER_CALC_DEPENDENCY z odpowiedzi XMLA (rowset) -> lista słowników."""
    if not xml:
        return None
    out = []
    for blok in re.findall(r"<row[^>]*>(.*?)</row>", xml, re.S):
        w = {}
        for tag, wart in re.findall(r"<([A-Za-z0-9_]+)>(.*?)</\1>", blok, re.S):
            w[_DEK.sub(lambda m: chr(int(m.group(1), 16)), tag)] = html.unescape(wart)
        out.append(w)
    return out
