# Użycie

## Panel w Power BI Desktop

1. Otwórz w Power BI Desktop zapisany raport (`.pbix` albo `.pbip`).
2. Kliknij **Narzędzia zewnętrzne → Standardy wizualizacji**. Panel przykleja się do prawej krawędzi tego okna
   Power BI i pokazuje postęp w trzech krokach: **Raport** (rozpoznanie pliku), **Model** (typy kolumn, jeśli model
   jest lokalny), **Standardy** (reguły).
3. U góry jest ocena ogólna i oceny wybranych standardów (0–100):

   | Ocena | Opis w panelu |
   |---|---|
   | 85–100 | dobra |
   | 60–84 | do poprawy |
   | 0–59 | słaba |

   Jak liczy się ocena — zob. [Ocena i konfiguracja](ocena-i-konfiguracja.md).

![Panel: problemy i oceny standardów](panel-problemy.png)

### Zakładka Problemy

- Kliknięcie standardu na liście ocen pokazuje tylko jego problemy.
- Filtry: waga (błędy, ostrzeżenia, info) i standard; pole **Szukaj** przeszukuje strony, wizualizacje i reguły.
- Po rozwinięciu reguły: **dlaczego** to problem, **jak naprawić**, źródło i lista wystąpień (strona › wizualizacja).

### Zakładka Strony

- Szkic każdej strony z obrysami wizualizacji, które mają uwagi. Kliknięcie prostokąta pokazuje uwagi do tej
  wizualizacji.
- **Pokaż prawdziwy wygląd** — zrzut strony prosto z Power BI Desktop (wymaga Node.js i `npm install`, zob.
  [Instalacja](instalacja.md)).

### Zakładka Standardy

![Zakładka Standardy](panel-standardy.png)

- Zaznacz standardy, które chcesz sprawdzać. Rozwiń standard, żeby wyłączyć pojedyncze reguły.
- Gotowe profile:

  | Profil | Standardy |
  |---|---|
  | **Podstawowy** (domyślny) | dostępność, percepcja, układ, spójność, dashboard |
  | **Raport zarządczy (IBCS)** | IBCS, percepcja, minimalizm, spójność, dostępność |
  | **Dostępność** | dostępność |
  | **Wszystkie** | wszystkie osiem standardów |

- Zmiana wyboru działa od razu: silnik zawsze sprawdza wszystkie reguły, a panel tylko filtruje widok i przelicza
  ocenę. Wybór jest zapamiętywany dla kolejnych raportów.

### Przyciski

| Przycisk | Działanie |
|---|---|
| **⟳** | sprawdź ponownie — także **F5** albo ponowne kliknięcie przycisku na wstążce |
| **szerzej / węziej** | przełącza szerokość panelu (460 ↔ 720 px) |
| **zwiń do paska** | wąski pasek z oceną; kliknięcie paska rozwija panel |
| **odepnij / przypnij** | zwykłe, przesuwalne okno albo panel przyklejony do Power BI (pozycja okna jest zapamiętywana) |
| **zamknij** | zamyka panel |
| **Kopiuj listę zadań** | kopiuje problemy z wybranych standardów z instrukcją naprawy (Markdown) |
| **folder** | otwiera folder z wynikami (`wynik.json`, `zadania.md`) |

### Dobrze wiedzieć

- **Raport jest czytany z pliku na dysku.** Gdy w Power BI są niezapisane zmiany (wykrywa je Desktop Bridge), panel
  to pokazuje. Zapisz (**Ctrl+S**) i kliknij **⟳**.
- **Jeden panel na okno Power BI.** Ponowne kliknięcie przycisku w tym samym oknie odświeża istniejący panel, zamiast
  otwierać drugi. Panel zamyka się razem z oknem Power BI.
- **Lista zadań** ma nagłówek z oceną, a dalej reguły od najpoważniejszych: „Jak naprawić” i do 40 wystąpień na
  regułę. Nadaje się do wklejenia w asystenta AI albo do zgłoszenia.

## Wiersz poleceń

Silnik działa także bez Power BI, np. na projekcie `.pbip` w repozytorium albo w CI.

```powershell
python standardy.py --lista                                              # standardy, profile i reguły
python standardy.py --raport przyklad\Demo.Report --profil wszystkie     # raport demonstracyjny
python standardy.py --raport "C:\raporty\Sprzedaz.pbip" --standardy wcag,uklad --wylaczone WCAG-04
python standardy.py --raport "C:\raporty\Sprzedaz.pbix" --profil ibcs --wyjscie .\wyniki
```

| Opcja | Znaczenie |
|---|---|
| `--raport` | `.pbip`, `.pbix` (także `.pbit`) albo folder `*.Report` |
| `--model` | TMSL modelu (JSON) — typy kolumn poprawiają rozpoznanie osi czasu |
| `--standardy` | identyfikatory standardów po przecinku: `wcag`, `percepcja`, `ibcs`, `minimalizm`, `dashboard`, `uklad`, `spojnosc`, `microsoft` |
| `--profil` | `podstawowy`, `ibcs`, `dostepnosc`, `wszystkie` (ignorowany, gdy podano `--standardy`) |
| `--wylaczone` | identyfikatory reguł do pominięcia, np. `IBCS-05,TUF-02` |
| `--wybor` | plik JSON `{"standardy": [...], "wylaczone": [...]}`; opcje `--standardy` i `--wylaczone` mają pierwszeństwo |
| `--wyjscie` | folder wyników (domyślnie `%TEMP%\StandardyWizualizacji\<raport>`) |
| `--konfiguracja` | plik progów (domyślnie `konfiguracja.json` w folderze narzędzia) |
| `--desktop`, `--zrodlo` | stan Desktopa i opis instancji — przekazuje je `analiza.ps1` |
| `--lista` | wypisuje standardy, profile i reguły |

Bez wyboru standardów działa profil **Podstawowy**. Kod wyjścia: `0` — sprawdzono (także gdy są problemy), `2` — nie
udało się odczytać raportu albo błędne opcje. Ostatnia linia wyjścia to `WYNIK: <ścieżka do wynik.json>`.

### Raport otwarty w Desktopie, bez panelu

`analiza.ps1` robi to samo co panel: rozpoznaje plik, czyta model przez TOM i uruchamia silnik.

```powershell
powershell -File .\analiza.ps1 -DesktopPid (Get-Process PBIDesktop | Select-Object -First 1).Id
powershell -File .\analiza.ps1 -Raport "C:\raporty\Sprzedaz.pbip"
```

## Pliki wynikowe

W folderze wyników (domyślnie `%TEMP%\StandardyWizualizacji\<raport>\`):

| Plik | Zawartość |
|---|---|
| `wynik.json` | znaleziska **wszystkich** reguł, oceny, geometria stron — format opisuje [Architektura](architektura.md#wynikjson) |
| `zadania.md` | lista zadań dla standardów z wywołania (z panelu: profil Podstawowy). Przycisk **Kopiuj listę zadań** uwzględnia bieżący wybór w panelu |

Panel zapisuje ustawienia i dziennik w `%LOCALAPPDATA%\StandardyWizualizacji\` (`ustawienia.json`, `okno.log`).

## Raport demonstracyjny

`przyklad/Demo.Report` to syntetyczna definicja raportu PBIR, służy do wiersza poleceń i testów. Nie ma pliku
`.pbip` ani modelu, więc nie otworzysz jej w Power BI Desktop.

- Strona **„Przed — wiele problemów”**: 11 wizualizacji z celowymi naruszeniami — wykres kołowy, oś słupków od
  1000, miesiące na osi pionowej, linia dla regionów, szary tekst 8 pt, brak tekstu alternatywnego, miernik,
  nachodzące na siebie tabele, wizualizacje poza kanwą.
- Strona **„Po — sprzedaż wg regionów”**: 3 wizualizacje bez uwag.

```powershell
python standardy.py --raport przyklad\Demo.Report --profil wszystkie
```
