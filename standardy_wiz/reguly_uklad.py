"""Układ i Gestalt — porządek na stronie (te same definicje co metryki E1–E7 skilla ocena-percepcyjna-raportu)."""
from __future__ import annotations

import itertools

from .katalog import pl, regula

GESTALT = "Zasady Gestalt; Ngo, Teo, Byrne 2003"


@regula("UKL-01", "uklad", "blad", "Wizualizacje w granicach kanwy",
        "Część wizualizacji poza kanwą jest ucięta w usłudze i w aplikacji mobilnej; element cały poza kanwą jest "
        "niewidoczny, ale wciąż wykonuje zapytanie.",
        "Przesuń albo zmniejsz wizualizację; element odłożony poza kanwę usuń.",
        GESTALT)
def ukl01(ctx):
    for s in ctx.strony():
        for w in s.widoczne():
            if w.x < -1 or w.y < -1 or w.x + w.w > s.w + 1 or w.y + w.h > s.h + 1:
                cala = w.x >= s.w or w.y >= s.h or w.x + w.w <= 0 or w.y + w.h <= 0
                if cala:
                    yield ctx.problem_wiz(s, w, "UKL-01", f"Cała poza kanwą ({w.x:g}, {w.y:g}) — niewidoczna.", waga="info")
                else:
                    yield ctx.problem_wiz(s, w, "UKL-01", f"Wychodzi poza kanwę {s.w:g}×{s.h:g} — ucięta.")


@regula("UKL-02", "uklad", "ostrzezenie", "Wizualizacje nie nachodzą na siebie",
        "Nakładające się wizualizacje zasłaniają dane i przechwytują kliknięcia (filtrowanie działa na tej wyżej).",
        "Rozsuń wizualizacje; świadome przełączanie widoków rób zakładkami.",
        GESTALT)
def ukl02(ctx):
    for s in ctx.strony():
        el = ctx.dane(s) + ctx.fragmentatory(s)
        for a, b in itertools.combinations(el, 2):
            ix = min(a.x + a.w, b.x + b.w) - max(a.x, b.x)
            iy = min(a.y + a.h, b.y + b.h) - max(a.y, b.y)
            if ix > 0 and iy > 0:
                u = ix * iy / max(1.0, min(a.w * a.h, b.w * b.h))
                if u > 0.005:
                    yield ctx.problem_wiz(s, a, "UKL-02", f"Nachodzi na „{b.etykieta}” ({u:.0%} mniejszej).",
                                          waga="" if u >= 0.05 else "info")


@regula("UKL-03", "uklad", "info", "Krawędzie wyrównane",
        "Oko łączy elementy leżące na wspólnej linii w grupę; krawędzie „prawie wyrównane” wyglądają jak błąd składu.",
        "Pozycje z siatki albo z pliku towarzyszącego tła (zones[] → position); rząd kart: równe szerokości i odstępy.",
        GESTALT)
def ukl03(ctx):
    for s in ctx.strony():
        el = ctx.tresc(s)
        if len(el) < 2:
            continue
        rama = ctx.obszar(s)
        tol = ctx.prog("tolerancja_px", 2.0)
        kraw = []
        for v in el:
            kraw += [("L", v.x, v), ("R", v.x + v.w, v), ("T", v.y, v), ("B", v.y + v.h, v)]
        gran = {"L": rama[0], "R": rama[2], "T": rama[1], "B": rama[3]}
        wyr = {i for i, (t, p, v) in enumerate(kraw)
               if abs(p - gran[t]) <= tol or any(t2 == t and v2 is not v and abs(p2 - p) <= tol for t2, p2, v2 in kraw)}
        for v in el:
            for poziomo in (True, False):
                if poziomo:
                    gr = sorted((u for u in el if abs(u.y - v.y) <= tol and abs(u.h - v.h) <= tol), key=lambda u: u.x)
                    rozm, odst, typy = [u.w for u in gr], [b.x - (a.x + a.w) for a, b in zip(gr, gr[1:])], ("L", "R")
                else:
                    gr = sorted((u for u in el if abs(u.x - v.x) <= tol and abs(u.w - v.w) <= tol), key=lambda u: u.y)
                    rozm, odst, typy = [u.h for u in gr], [b.y - (a.y + a.h) for a, b in zip(gr, gr[1:])], ("T", "B")
                if len(gr) >= 2 and max(rozm) - min(rozm) <= 3 and min(odst) >= -tol and max(odst) - min(odst) <= 3:
                    wyr |= {i for i, (t, _, u) in enumerate(kraw) if u in gr and t in typy}
        udzial = len(wyr) / len(kraw)
        if udzial < 0.8:
            samotne = [f"{v.nazwa}.{t}={p:g}" for i, (t, p, v) in enumerate(kraw) if i not in wyr]
            yield ctx.problem_str(s, "UKL-03", f"Wyrównanych {udzial:.0%} krawędzi; niewyrównane: "
                                  + ", ".join(samotne[:8]) + ("…" if len(samotne) > 8 else ""),
                                  waga="ostrzezenie" if udzial < 0.6 else "")


@regula("UKL-04", "uklad", "info", "Rytm odstępów",
        "Zasada bliskości: jeden odstęp wewnątrz grup i ewentualnie drugi, większy, między grupami. Kilka różnych "
        "odstępów rozbija grupowanie.",
        "Jeden odstęp między kafelkami (np. 16 px), większy tylko między sekcjami.",
        GESTALT)
def ukl04(ctx):
    for s in ctx.strony():
        el = ctx.dane(s)
        gaps = []
        for a, b in itertools.permutations(el, 2):
            g = b.x - (a.x + a.w)
            if 0.5 < g <= 64 and min(a.y + a.h, b.y + b.h) - max(a.y, b.y) > 0.3 * min(a.h, b.h) and not any(
                    c is not a and c is not b and c.x >= a.x + a.w - 1 and c.x + c.w <= b.x + 1
                    and min(c.y + c.h, a.y + a.h) - max(c.y, a.y) > 0 for c in el):
                gaps.append(g)
            g = b.y - (a.y + a.h)
            if 0.5 < g <= 64 and min(a.x + a.w, b.x + b.w) - max(a.x, b.x) > 0.3 * min(a.w, b.w) and not any(
                    c is not a and c is not b and c.y >= a.y + a.h - 1 and c.y + c.h <= b.y + 1
                    and min(c.x + c.w, a.x + a.w) - max(c.x, a.x) > 0 for c in el):
                gaps.append(g)
        klastry = []
        for g in sorted(gaps):
            if klastry and g - klastry[-1][-1] <= 2.5:
                klastry[-1].append(g)
            else:
                klastry.append([g])
        if len(klastry) >= 3:
            opis = ", ".join(f"{sum(k) / len(k):.0f} px ×{len(k)}" for k in klastry)
            yield ctx.problem_str(s, "UKL-04", f"{len(klastry)} różne odstępy między wizualizacjami: {opis}.",
                                  waga="ostrzezenie" if len(klastry) >= 4 else "")


@regula("UKL-05", "uklad", "info", "Równowaga strony",
        "Gdy ciężar treści (pola wizualizacji) jest przesunięty do jednej krawędzi, strona wygląda na niedokończoną.",
        "Rozłóż duże wizualizacje; pusta połowa strony → powiększ kafelki albo zmień układ.",
        GESTALT + " (equilibrium)")
def ukl05(ctx):
    for s in ctx.strony():
        el = ctx.tresc(s)
        if not el:
            continue
        x0, y0, x1, y1 = ctx.obszar(s)
        pole = sum(v.w * v.h for v in el) or 1.0
        sx = sum(v.w * v.h * (v.x + v.w / 2) for v in el) / pole
        sy = sum(v.w * v.h * (v.y + v.h / 2) for v in el) / pole
        ex = (sx - (x0 + x1) / 2) / max(1.0, (x1 - x0) / 2)
        ey = (sy - (y0 + y1) / 2) / max(1.0, (y1 - y0) / 2)
        r = 1 - (min(1.0, abs(ex)) + min(1.0, abs(ey))) / 2
        if r < 0.85:
            kier = [k for k, war in (("w lewo", ex < -0.15), ("w prawo", ex > 0.15), ("w górę", ey < -0.15),
                                     ("w dół", ey > 0.15)) if war]
            yield ctx.problem_str(s, "UKL-05", f"Równowaga {pl(r, 2)} — ciężar przesunięty {' i '.join(kier) or 'od środka'}.")


@regula("UKL-06", "uklad", "info", "Wykorzystany obszar roboczy",
        "Duża pusta przestrzeń przy małych wykresach marnuje ekran i zmniejsza czytelność danych.",
        "Powiększ kafelki do obszaru roboczego albo zmień układ strony.",
        GESTALT)
def ukl06(ctx):
    for s in ctx.strony():
        el = ctx.tresc(s)
        if not el:
            continue
        x0, y0, x1, y1 = ctx.obszar(s)
        fw, fh = int(x1 - x0), int(y1 - y0)
        if fw <= 0 or fh <= 0:
            continue
        krok = 4
        siatka = set()
        for v in el:
            for gx in range(int(max(0, v.x - x0)) // krok, int(min(fw, v.x + v.w - x0)) // krok):
                for gy in range(int(max(0, v.y - y0)) // krok, int(min(fh, v.y + v.h - y0)) // krok):
                    siatka.add((gx, gy))
        u = len(siatka) / max(1, (fw // krok) * (fh // krok))
        if u < 0.55:
            yield ctx.problem_str(s, "UKL-06", f"Wizualizacje wypełniają {u:.0%} obszaru roboczego.",
                                  waga="ostrzezenie" if u < 0.4 else "")


@regula("UKL-07", "uklad", "info", "KPI nad szczegółami",
        "Czytamy od góry i od lewej (skan F/Z): najważniejsze liczby powinny być pierwsze, szczegóły niżej.",
        "Karty KPI w górnym rzędzie obszaru roboczego, wykresy i tabele pod nimi.",
        GESTALT + "; Nielsen 2006 (F-pattern)")
def ukl07(ctx):
    for s in ctx.strony():
        dane = ctx.dane(s)
        karty = [v for v in dane if v.klasa == "karta"]
        szcz = [v for v in dane if v.klasa in ("wykres", "tabela")]
        if not karty or not szcz:
            continue
        gora = min(v.y for v in szcz)
        nizej = [v for v in karty if v.y > gora + 8]
        if nizej:
            yield ctx.problem_str(s, "UKL-07", f"{len(nizej)} z {len(karty)} kart KPI poniżej pierwszego wykresu: "
                                  + ", ".join(v.etykieta for v in nizej[:4]) + ".",
                                  waga="ostrzezenie" if len(nizej) == len(karty) else "")
