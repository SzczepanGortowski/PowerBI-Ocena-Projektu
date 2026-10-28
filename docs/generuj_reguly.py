"""Generuje docs/reguly.md z katalogu reguł silnika. Po zmianie reguły: python docs/generuj_reguly.py"""
import sys
from pathlib import Path

KORZEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORZEN))

from standardy_wiz import silnik  # noqa: E402,F401 (rejestracja reguł)
from standardy_wiz.katalog import PROFILE, PUNKTY, REGULY, STANDARDY, WAGI  # noqa: E402

PLIK = KORZEN / "docs" / "reguly.md"


def tresc() -> str:
    lin = ["# Katalog reguł", "",
           "> Plik generowany z kodu (`python docs/generuj_reguly.py`) — nie edytuj go ręcznie. Teksty reguł są w",
           "> `standardy_wiz/reguly_<standard>.py` (dekorator `@regula`).", "",
           f"{len(REGULY)} reguł w {len(STANDARDY)} standardach. Te same teksty — „dlaczego”, „jak naprawić” i źródło — "
           "panel pokazuje po rozwinięciu reguły na liście problemów.", "",
           "Waga reguły: " + ", ".join(f"**{WAGI[w]}** ({p} pkt)" for w, p in PUNKTY.items())
           + ". Pojedyncze znalezisko może mieć wagę wyższą albo niższą niż reguła (np. kontrast poniżej 3:1 to błąd) — "
           "zob. [Ocena i konfiguracja](ocena-i-konfiguracja.md).", "",
           "| Standard | Identyfikator | Reguły | W profilach |", "|---|---|---|---|"]
    for s in STANDARDY.values():
        profile = ", ".join(p["nazwa"] for p in PROFILE.values() if s.id in p["standardy"])
        lin.append(f"| [{s.nazwa}](#{s.id}) | `{s.id}` | {len(s.reguly)} | {profile} |")
    for s in STANDARDY.values():
        lin += ["", f'<a id="{s.id}"></a>', "", f"## {s.nazwa}", "", s.opis, "", f"Źródła: {s.zrodlo}.", "",
                "| Reguła | Co sprawdza | Waga |", "|---|---|---|"]
        lin += [f"| [`{rid}`](#{rid.lower()}) | {REGULY[rid].tytul} | {WAGI[REGULY[rid].waga]} |" for rid in s.reguly]
        for rid in s.reguly:
            r = REGULY[rid]
            lin += ["", f'<a id="{rid.lower()}"></a>', "", f"### {rid} · {r.tytul}", "",
                    f"**Waga:** {WAGI[r.waga]}" + (f" · **Źródło:** {r.zrodlo}" if r.zrodlo else ""), ""]
            if r.wymaga == "model":
                lin += ["**Model:** typy kolumn z modelu poprawiają trafność; bez modelu reguła rozpoznaje oś czasu "
                        "z nazw pól.", ""]
            lin += [f"**Dlaczego:** {r.dlaczego}", "", f"**Jak naprawić:** {r.jak}"]
    return "\n".join(lin) + "\n"


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    PLIK.write_text(tresc(), encoding="utf-8", newline="\n")
    print(f"Zapisano {PLIK.relative_to(KORZEN)} ({len(REGULY)} reguł)")
