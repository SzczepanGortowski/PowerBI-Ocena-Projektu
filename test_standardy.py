"""Testy silnika Standardów wizualizacji: syntetyczny raport PBIR z celowymi naruszeniami + czysta strona.

Uruchom: .venv\\Scripts\\python.exe -m unittest discover -s narzedzia\\standardy-wizualizacji\\testy -v
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from standardy_wiz import kolor  # noqa: E402
from standardy_wiz.katalog import REGULY, STANDARDY  # noqa: E402
from standardy_wiz.silnik import markdown, oceny, wynik  # noqa: E402


def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def kol(encja, nazwa):
    return {"field": {"Column": {"Expression": {"SourceRef": {"Entity": encja}}, "Property": nazwa}},
            "queryRef": f"{encja}.{nazwa}"}


def miara(encja, nazwa):
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": encja}}, "Property": nazwa}},
            "queryRef": f"{encja}.{nazwa}"}


def wiz(nazwa, typ, x, y, w, h, role=None, obiekty=None, kontener=None, tab=0, sort=None):
    v = {"visualType": typ, "query": {"queryState": {r: {"projections": p} for r, p in (role or {}).items()}}}
    if sort:
        v["query"]["sortDefinition"] = {"sort": [sort]}
    if obiekty:
        v["objects"] = obiekty
    k = {"title": [{"properties": {"show": lit("true"), "text": lit(f"'Tytuł {nazwa}'")}}],
         "general": [{"properties": {"altText": lit(f"'Opis {nazwa}'")}}]}
    k.update(kontener or {})
    v["visualContainerObjects"] = k
    return {"name": nazwa, "position": {"x": x, "y": y, "z": 0, "width": w, "height": h, "tabOrder": tab}, "visual": v}


def tekst(nazwa, x, y, w, h, kolor_tekstu, pt="12pt"):
    return {"name": nazwa, "position": {"x": x, "y": y, "z": 0, "width": w, "height": h, "tabOrder": 0},
            "visual": {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": [
                {"textRuns": [{"value": "Tekst", "textStyle": {"fontSize": pt, "color": kolor_tekstu}}]}]}}]}}}


def zbuduj(folder: Path, strony):
    rep = folder / "Test.Report"
    (rep / "definition" / "pages").mkdir(parents=True)
    (rep / "definition.pbir").write_text(json.dumps({"version": "4.0", "datasetReference": {"byPath": {"path": "../Test.SemanticModel"}}}),
                                         encoding="utf-8")
    (rep / "definition" / "report.json").write_text(json.dumps({"themeCollection": {}}), encoding="utf-8")
    (rep / "definition" / "pages" / "pages.json").write_text(json.dumps({"pageOrder": [s[0] for s in strony]}), encoding="utf-8")
    for nazwa, tytul, rozmiar, wizualizacje in strony:
        p = rep / "definition" / "pages" / nazwa
        (p / "visuals").mkdir(parents=True)
        (p / "page.json").write_text(json.dumps({"name": nazwa, "displayName": tytul, "width": rozmiar[0], "height": rozmiar[1]}),
                                     encoding="utf-8")
        for v in wizualizacje:
            (p / "visuals" / v["name"]).mkdir()
            (p / "visuals" / v["name"] / "visual.json").write_text(json.dumps(v), encoding="utf-8")
    return rep


ZLA = [
    wiz("kolo", "pieChart", 20, 20, 300, 200, {"Category": [kol("Produkt", "Kategoria")], "Y": [miara("M", "Sprzedaż")]}),
    wiz("przycieta", "clusteredColumnChart", 340, 20, 300, 200,
        {"Category": [kol("Sklep", "Region")], "Y": [miara("M", "Sprzedaż")]},
        {"valueAxis": [{"properties": {"start": lit("1000D")}}]}),
    wiz("czasPoziomo", "barChart", 660, 20, 300, 200, {"Category": [kol("Kalendarz", "Miesiąc")], "Y": [miara("M", "Marża")]}),
    wiz("liniaRegiony", "lineChart", 980, 20, 280, 200, {"Category": [kol("Sklep", "Region")], "Y": [miara("M", "Sprzedaż")]}),
    tekst("szaryTekst", 20, 240, 300, 40, "#bfbfbf", "8pt"),
    wiz("bezAlt", "clusteredColumnChart", 340, 240, 300, 200, {"Category": [kol("Sklep", "Format")], "Y": [miara("M", "Sprzedaż")]},
        {"dataPoint": [{"properties": {"fill": {"solid": {"color": lit("'#ff0000'")}}}, "selector": {"metadata": "M.Sprzedaż"}}]},
        {"general": [{"properties": {}}]}),
    wiz("altMiara", "clusteredColumnChart", 660, 240, 300, 200, {"Category": [kol("Sklep", "Format")], "Y": [miara("M", "Sprzedaż")]},
        kontener={"general": [{"properties": {"altText": {"expr": {"Measure": {"Expression": {"SourceRef": {"Entity": "M"}},
                                                                                "Property": "Alt"}}}}}]}),
    wiz("miernik", "gauge", 980, 240, 280, 200, {"Y": [miara("M", "Sprzedaż")]}),
    wiz("nachodzi", "tableEx", 600, 400, 300, 200, {"Values": [kol("Sklep", "Nazwa")]}),
    wiz("poKanwie", "tableEx", 1100, 600, 300, 200, {"Values": [kol("Sklep", "Nazwa")]}),
    wiz("zaKanwa", "cardVisual", 50, 900, 200, 50, {"Data": [miara("M", "Sprzedaż")]}),
]
CZYSTA = [
    wiz("lewy", "clusteredColumnChart", 40, 40, 592, 300, {"Category": [kol("Sklep", "Region")], "Y": [miara("M", "Sprzedaż")]},
        {"labels": [{"properties": {"show": lit("true")}}], "valueAxis": [{"properties": {"show": lit("false")}}]}, tab=0),
    wiz("prawy", "clusteredColumnChart", 648, 40, 592, 300, {"Category": [kol("Sklep", "Format")], "Y": [miara("M", "Marża")]},
        {"labels": [{"properties": {"show": lit("true")}}], "valueAxis": [{"properties": {"show": lit("false")}}]}, tab=1),
    wiz("dol", "lineChart", 40, 356, 1200, 324, {"Category": [kol("Kalendarz", "Data")], "Y": [miara("M", "Sprzedaż")]}, tab=2),
]


class TestKolor(unittest.TestCase):
    def test_ciede2000_referencja_sharma(self):
        self.assertAlmostEqual(kolor.ciede2000((50, 2.6772, -79.7751), (50, 0, -82.7485)), 2.0425, places=4)
        self.assertAlmostEqual(kolor.ciede2000((50, 2.5, 0), (73, 25, -18)), 27.1492, places=4)

    def test_kontrast(self):
        self.assertAlmostEqual(kolor.kontrast("#000000", "#ffffff"), 21.0, places=6)
        self.assertLess(kolor.kontrast("#bfbfbf", "#ffffff"), 2.0)

    def test_daltonizm_czerwony_zielony(self):
        d, _, _ = kolor.min_delta_e(["#e15759", "#59a14f"], "deuteranopia")
        self.assertLess(d, 3)


class TestReguly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        rep = zbuduj(Path(cls.tmp.name), [("zla", "Strona 1", (1280, 720), ZLA),
                                          ("czysta", "Sprzedaż wg regionów", (1280, 720), CZYSTA),
                                          ("podpowiedz", "Podpowiedź", (320, 240), [wiz("p", "pieChart", 0, 0, 300, 200)])])
        cls.w = wynik(str(rep), profil="wszystkie")
        cls.zla = [p for p in cls.w["problemy"] if p.get("id_strony") == "zla" or p["typ_obiektu"] == "raport"]
        cls.czysta = [p for p in cls.w["problemy"] if p.get("id_strony") == "czysta"]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def znajdz(self, rid, wiz=None, lista=None):
        return [p for p in (lista if lista is not None else self.zla)
                if p["regula"] == rid and (wiz is None or p.get("id_wizualizacji") == wiz)]

    def test_brak_bledow_regul(self):
        self.assertEqual(self.w["bledy_regul"], [])

    def test_kanal_kola_i_miernika(self):
        self.assertTrue(self.znajdz("PERC-01", "kolo"))
        self.assertTrue(self.znajdz("IBCS-01", "kolo"))
        self.assertTrue(self.znajdz("FEW-03", "miernik"))

    def test_os_od_zera(self):
        for rid in ("PERC-02", "IBCS-07"):
            p = self.znajdz(rid, "przycieta")
            self.assertTrue(p, rid)
            self.assertEqual(p[0]["waga"], "blad")
            self.assertIn("1 000", p[0]["opis"])          # liczba z separatorem tysięcy

    def test_czas_i_linie_ibcs(self):
        self.assertTrue(self.znajdz("IBCS-02", "czasPoziomo"))
        self.assertTrue(self.znajdz("IBCS-03", "liniaRegiony"))
        self.assertFalse(self.znajdz("IBCS-03", "dol", self.czysta))

    def test_kontrast_i_rozmiar_tekstu(self):
        p = self.znajdz("WCAG-01", "szaryTekst")
        self.assertTrue(p)
        self.assertEqual(p[0]["waga"], "blad")
        self.assertTrue(self.znajdz("WCAG-05", "szaryTekst"))

    def test_tekst_alternatywny_staly_i_z_miary(self):
        self.assertTrue(self.znajdz("WCAG-04", "bezAlt"))
        self.assertFalse(self.znajdz("WCAG-04", "altMiara"))
        self.assertFalse(self.znajdz("WCAG-04", "kolo"))

    def test_kolor_miary_na_stronie_i_w_raporcie(self):
        self.assertTrue(self.znajdz("PERC-08"))
        self.assertTrue([p for p in self.w["problemy"] if p["regula"] == "SPJ-02"])

    def test_uklad(self):
        self.assertTrue(self.znajdz("UKL-02"))
        uciete = self.znajdz("UKL-01", "poKanwie")
        self.assertTrue(uciete and uciete[0]["waga"] == "blad")
        niewidoczne = self.znajdz("UKL-01", "zaKanwa")
        self.assertTrue(niewidoczne and niewidoczne[0]["waga"] == "info")

    def test_dashboard_i_microsoft(self):
        self.assertTrue(self.znajdz("FEW-01"))
        self.assertTrue(self.znajdz("MS-01"))
        self.assertTrue(self.znajdz("WCAG-06"))      # wszystkie tabOrder = 0

    def test_czysta_strona(self):
        istotne = [p for p in self.czysta if p["regula"].split("-")[0] in ("PERC", "IBCS", "UKL", "TUF", "FEW", "WCAG")]
        self.assertEqual(istotne, [], [f"{p['regula']} {p['obiekt']}: {p['opis']}" for p in istotne])

    def test_strona_podpowiedzi_pominieta(self):
        self.assertFalse([p for p in self.w["problemy"] if p.get("id_strony") == "podpowiedz"])
        self.assertNotIn("podpowiedz", [s["nazwa"] for s in self.w["strony"]])

    def test_wybor_standardow(self):
        status = {r: x["status"] for r, x in self.w["reguly"].items()}
        oc, ogolna = oceny(self.w["problemy"], ["wcag"], set(), status)
        self.assertEqual(list(oc), ["wcag"])
        self.assertIsNotNone(ogolna)
        oc2, _ = oceny(self.w["problemy"], ["wcag"], {"WCAG-01", "WCAG-04", "WCAG-05", "WCAG-06", "WCAG-07"}, status)
        self.assertGreater(oc2["wcag"]["punkty"], oc["wcag"]["punkty"])
        md = markdown(self.w, ["ibcs"], set())
        self.assertIn("IBCS-01", md)
        self.assertNotIn("WCAG-01", md)

    def test_katalog(self):
        for s in STANDARDY.values():
            self.assertTrue(s.reguly, s.id)
        for r in REGULY.values():
            self.assertIn(r.waga, ("blad", "ostrzezenie", "info"))
            self.assertTrue(r.dlaczego and r.jak and r.zrodlo, r.id)


if __name__ == "__main__":
    unittest.main()
