# Rozwijanie

## Środowisko

Silnik potrzebuje tylko Pythona 3.9+ z biblioteką standardową. Środowisko wirtualne nie jest wymagane, ale jeśli je
założysz jako `.venv` w folderze narzędzia, panel użyje właśnie jego.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m unittest discover -s testy -v
```

## Testy

```powershell
python -m unittest discover -s testy -v
```

`testy/test_standardy.py` buduje w folderze tymczasowym syntetyczny raport PBIR z trzema stronami:

- **zla** — wizualizacje z celowymi naruszeniami, które testy muszą wykryć,
- **czysta** — strona, na której reguły percepcji, IBCS, układu, Tufte, Few i WCAG nie mogą nic znaleźć,
- **podpowiedz** — mała strona podpowiedzi, która musi zostać pominięta.

Do tego testy kolorymetrii (CIEDE2000 na wartościach referencyjnych Sharmy, kontrast WCAG, symulacja daltonizmu),
wyboru standardów i oceny oraz test, który pilnuje, żeby [docs/reguly.md](reguly.md) zgadzał się z kodem.

## Nowa reguła

1. Dopisz funkcję z dekoratorem `@regula` w pliku `standardy_wiz/reguly_<standard>.py`. Funkcja dostaje
   `ctx` (`Kontekst`) i zwraca (albo `yield`) znaleziska:

   ```python
   @regula("FEW-03", "dashboard", "ostrzezenie", "Bez mierników (gauge)",
           "Miernik zajmuje dużo miejsca, a pokazuje jedną liczbę i kąt, który trudno porównać z innymi.",
           "Karta z wartością i odchyleniem od celu albo wykres pociskowy (bullet).",
           FEW)
   def few03(ctx):
       for s in ctx.strony():
           for w in s.widoczne():
               if w.typ == "gauge":
                   yield ctx.problem_wiz(s, w, "FEW-03", "Miernik (gauge).")
   ```

   Argumenty dekoratora: identyfikator, standard, waga (`blad`, `ostrzezenie`, `info`), tytuł, dlaczego, jak
   naprawić, źródło i opcjonalnie `wymaga="model"`, gdy model poprawia trafność reguły.

2. Znalezisko twórz przez:

   | Funkcja | Dotyczy |
   |---|---|
   | `ctx.problem_wiz(s, w, rid, opis, waga="")` | wizualizacji `w` na stronie `s` (obrys na szkicu strony) |
   | `ctx.problem_str(s, rid, opis, waga="")` | całej strony |
   | `ctx.problem_rap(rid, opis, obiekt="", waga="")` | całego raportu |

   Pusta `waga` = waga reguły. Podaj inną, gdy dane znalezisko jest wyraźnie poważniejsze albo mniej pewne.

3. Dodaj przypadek do testu: wizualizację wyzwalającą regułę w `ZLA` i asercję w `TestReguly`. Strona `CZYSTA`
   nadal nie może nic zgłaszać.
4. Wygeneruj katalog reguł i uruchom testy:

   ```powershell
   python docs/generuj_reguly.py
   python -m unittest discover -s testy -v
   ```

5. Zaktualizuj liczbę reguł w `README.md` (opis i streszczenie po angielsku).

Reguła nie może zatrzymać całej kontroli: wyjątek w regule trafia do `bledy_regul`, a reguła jest pomijana w ocenie.
Mimo to test `test_brak_bledow_regul` wymaga, żeby na raporcie testowym żadna reguła się nie wywróciła.

### Co daje `Kontekst`

| Metoda | Zwraca |
|---|---|
| `ctx.strony()` | strony do oceny (bez stron podpowiedzi) |
| `s.widoczne()` | widoczne wizualizacje strony |
| `ctx.dane(s)`, `ctx.fragmentatory(s)`, `ctx.tresc(s)` | wizualizacje danych, fragmentatory, cała treść strony |
| `ctx.obszar(s)`, `ctx.w_obszarze(s, w)` | obszar roboczy strony: obwiednia treści bez lewego paska nawigacji (przyciski, obrazy, kształty) |
| `ctx.wart(w, obiekt, wlasc)` | wartość formatowania po kaskadzie (wizualizacja → motyw → domyślna) |
| `ctx.efekt(w, obiekt, wlasc)` | to samo jako para `(wartość, skąd)`: `wizualizacja`, `motyw` albo `domyślna` |
| `ctx.teksty(w)`, `ctx.tlo(s, w)` | elementy tekstowe `{element, pt, kroj, kolor, pogrubiony}`; efektywne tło |
| `ctx.kolory_serii(w)`, `ctx.kolory_miar(w)`, `ctx.kolory_danych()` | kolory serii i miar, paleta motywu |
| `ctx.kategorie(w)`, `ctx.miary(w)`, `ctx.os_wartosci(w)` | pola na osiach, miary, ustawienia osi wartości |
| `ctx.czy_czas(p)`, `ctx.czy_ciagla(p)`, `ctx.czy_porzadkowa(p)` | rodzaj pola — z typów kolumn modelu albo z nazwy |
| `ctx.prog(nazwa, domyslny)` | próg z `konfiguracja.json` |
| `ctx.model` | model (`None`, gdy niedostępny) |

Kolorymetria (kontrast, ΔE2000, symulacja daltonizmu) jest w `standardy_wiz/kolor.py`.

## Nowy standard

1. `_standard(id, nazwa, krotko, opis, zrodlo)` w `standardy_wiz/katalog.py`.
2. Nowy plik `standardy_wiz/reguly_<id>.py` z regułami i jego import w `standardy_wiz/silnik.py` (import rejestruje
   reguły).
3. Opcjonalnie wpis w `PROFILE` w `katalog.py`.
4. Testy, `python docs/generuj_reguly.py` i tabela standardów w `README.md`.

Panel nie wymaga zmian: listę standardów, reguł i profili dostaje w `wynik.json`.

## Interfejs panelu

`app/index.html`, `app/app.css` i `app/app.js` to zwykła strona bez zależności i bez budowania. Poza WebView2
(bez gospodarza) komunikaty do gospodarza trafiają do konsoli (`→ gospodarz …`). W panelu działają narzędzia
deweloperskie WebView2 (**F12**). Ikony z `app/ikony` gospodarz wysyła panelowi w komunikacie `start` — nowa ikona
musi trafić także do listy `$IKONY` w `okno.ps1`.

Protokół komunikatów i format `wynik.json` opisuje [Architektura](architektura.md).

## Pułapki PowerShell 5.1

Power BI Desktop uruchamia narzędzie przez Windows PowerShell 5.1, więc:

- pliki `.ps1` muszą być w **UTF-8 z BOM** — bez BOM PowerShell czyta je w stronie kodowej systemu i polskie znaki
  psują napisy, a nawet składnię;
- polski cudzysłów („ ”) w napisie działa jak ogranicznik napisu;
- pusty argument `""` z linii poleceń znika — dlatego `uruchom.ps1` sam parsuje `$args`, a `okno.ps1` nie przekazuje
  pustych wartości dalej;
- Python ze Sklepu Microsoft wirtualizuje zapisy do `%LOCALAPPDATA%`, więc wymiana plików między silnikiem
  a panelem idzie przez `%TEMP%`.

Szybkie sprawdzenie składni wszystkich skryptów:

```powershell
Get-ChildItem *.ps1 | ForEach-Object {
  $e = $null
  [void][System.Management.Automation.Language.Parser]::ParseFile($_.FullName, [ref]$null, [ref]$e)
  '{0}: {1} błędów' -f $_.Name, $e.Count
}
```

## Wersja

Numer wersji jest w `package.json` i w `instaluj.ps1` (pole `version` rejestracji). Zmieniaj oba razem.
