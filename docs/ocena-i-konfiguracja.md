# Ocena i konfiguracja

## Jak liczy się ocena

Każdy wybrany standard startuje od **100 punktów**. Każda naruszona reguła odejmuje:

```
kara = min( punkty_wagi × (1 + log₂ liczby_wystąpień),  3 × punkty_wagi )
```

| Waga | Punkty wagi | Kara przy 1 / 2 / 3 / 4+ wystąpieniach |
|---|---|---|
| błąd | 10 | 10 / 20 / 25,8 / 30 |
| ostrzeżenie | 4 | 4 / 8 / 10,3 / 12 |
| info | 1 | 1 / 2 / 2,6 / 3 |

- Logarytm sprawia, że pierwsze wystąpienie kosztuje najwięcej, a powtórzenia tej samej reguły coraz mniej. Od
  czterech wystąpień kara już nie rośnie, więc jedna masowo łamana reguła nie zeruje oceny.
- Kara liczy się osobno dla każdej pary **(reguła, waga)**: jeśli reguła dała jedno znalezisko jako błąd i dwa jako
  ostrzeżenie, to są dwie kary.
- Ocena standardu nie spada poniżej 0 i jest zaokrąglana do liczby całkowitej.
- **Ocena ogólna** to średnia ocen wybranych standardów.
- Wyłączona reguła nie liczy się do oceny i znika z listy problemów. Standard z wszystkimi regułami wyłączonymi
  ma ocenę „—” i nie wchodzi do średniej.
- Reguła, która zakończyła się błędem programu, nie liczy się do oceny. Jej opis trafia do `bledy_regul`
  w `wynik.json`, a kontrola pozostałych reguł trwa dalej.

**Przykład** (standard Dostępność): jeden tekst o kontraście poniżej 3:1 (`WCAG-01`, błąd), dwa za małe teksty
(`WCAG-05`, ostrzeżenie) i trzy wizualizacje bez tekstu alternatywnego (`WCAG-04`, info):

```
100 − 10 − 8 − 2,6 = 79,4  →  79
```

Panel liczy ocenę tym samym wzorem w przeglądarce, dlatego zmiana wyboru standardów nie wymaga ponownego
sprawdzania.

### Waga znaleziska a waga reguły

Każda reguła ma wagę domyślną (zob. [Katalog reguł](reguly.md)), ale pojedyncze znalezisko może ją podnieść albo
obniżyć, gdy problem jest wyraźnie poważniejszy albo mniej pewny. Przykłady:

| Reguła | Waga reguły | Znalezisko |
|---|---|---|
| `WCAG-01` kontrast tekstu | ostrzeżenie | **błąd**, gdy kontrast < 3:1 |
| `FEW-01` liczba wizualizacji | ostrzeżenie | **błąd** powyżej progu `wizualizacje_blad` (12) |
| `MS-02` wizualizacje a wydajność | ostrzeżenie | **błąd** powyżej 25 wizualizacji wykonujących zapytania |
| `PERC-04` miary na wykresie | ostrzeżenie | **błąd** powyżej 6 miar |
| `IBCS-06` tytuł z komunikatem | info | **ostrzeżenie**, gdy wizualizacja nie ma tytułu |
| `WCAG-02`, `WCAG-03` | ostrzeżenie | **info**, gdy kolory serii są założone z palety motywu (liczby kategorii nie ma w definicji); `WCAG-02` także wtedy, gdy wartości podają etykiety danych |
| `WCAG-05` rozmiar tekstu | ostrzeżenie | **info**, gdy najmniejszy tekst jest najwyżej 1 pt poniżej progu |

Pełna logika jest w kodzie reguły (`standardy_wiz/reguly_<standard>.py`).

## Wybór standardów

| Gdzie | Jak |
|---|---|
| Panel | zakładka **Standardy** — standardy, pojedyncze reguły, profile; zapamiętywane w `%LOCALAPPDATA%\StandardyWizualizacji\ustawienia.json` |
| Wiersz poleceń | `--standardy`, `--profil`, `--wylaczone` albo plik `--wybor` — zob. [Użycie](uzycie.md#wiersz-poleceń) |

Kolejność w wierszu poleceń: `--standardy` → `--profil` → profil **Podstawowy**.

## Progi reguł — `konfiguracja.json`

```json
{
  "progi": {
    "tekst_min_pt": 9,
    "wizualizacje_max": 8,
    "wizualizacje_blad": 12,
    "wizualizacje_wydajnosc": 15,
    "tolerancja_px": 2.0,
    "pozycja_tolerancja_px": 4
  }
}
```

| Próg | Domyślnie | Reguła | Znaczenie |
|---|---|---|---|
| `tekst_min_pt` | 9 | `WCAG-05` | najmniejszy dopuszczalny rozmiar tekstu (pt) |
| `wizualizacje_max` | 8 | `FEW-01` | więcej wizualizacji danych na stronie → ostrzeżenie |
| `wizualizacje_blad` | 12 | `FEW-01` | więcej → błąd |
| `wizualizacje_wydajnosc` | 15 | `MS-02` | więcej wizualizacji wykonujących zapytania → ostrzeżenie (powyżej 25 zawsze błąd) |
| `tolerancja_px` | 2,0 | `UKL-03` | krawędzie bliżej niż tyle pikseli uznaje się za wyrównane |
| `pozycja_tolerancja_px` | 4 | `SPJ-01` | dopuszczalny rozrzut położenia fragmentatora między stronami (px) |

- Klucze zaczynające się od `$` (np. `$opis`) to komentarze i są pomijane.
- Brakujący próg = wartość domyślna z tabeli.
- Panel zawsze czyta `konfiguracja.json` z folderu narzędzia; w wierszu poleceń inny plik podasz przez
  `--konfiguracja`.
- Tytuły reguł podają wartości domyślne (np. „Najwyżej 8 wizualizacji danych na stronie”) i po zmianie progu się
  nie zmieniają. Bieżący próg widać w opisie znaleziska `FEW-01` i `WCAG-05`.
