# Rozwiązywanie problemów

## Gdzie szukać przyczyny

| Co | Gdzie |
|---|---|
| Dziennik panelu | `%LOCALAPPDATA%\StandardyWizualizacji\okno.log` |
| Wynik ostatniego sprawdzenia | `%TEMP%\StandardyWizualizacji\<raport>\wynik.json` (pola `ostrzezenia` i `bledy_regul`) |
| Postęp analizy | `%TEMP%\StandardyWizualizacji\postep-*.jsonl` |

Analiza uruchomiona ręcznie wypisuje wszystkie kroki i komunikaty silnika w konsoli:

```powershell
powershell -ExecutionPolicy Bypass -File .\analiza.ps1 -DesktopPid (Get-Process PBIDesktop | Select-Object -First 1).Id
```

## Najczęstsze sytuacje

| Objaw | Przyczyna | Co zrobić |
|---|---|---|
| Brak przycisku **Standardy wizualizacji** na wstążce | narzędzie nie jest zarejestrowane albo Desktop nie był uruchomiony ponownie | `.\instaluj.ps1`, potem zamknij **wszystkie** okna Power BI Desktop i otwórz ponownie. Sprawdź, czy plik `Standardy wizualizacji.pbitool.json` jest w `%CommonProgramFiles(x86)%\Microsoft Shared\Power BI Desktop\External Tools` |
| Przycisk jest, ale nic się nie dzieje | folder narzędzia przeniesiono albo usunięto | uruchom `.\instaluj.ps1` ponownie z nowego folderu |
| Okno „Nie udało się otworzyć panelu Standardy wizualizacji” | błąd przy starcie panelu | treść błędu jest w oknie i w `okno.log` |
| „Brak bibliotek WebView2 (folder bin Power BI Desktop)” | Power BI Desktop bez `WebView2Loader.dll` (stara wersja) | zaktualizuj Power BI Desktop |
| „Nie znaleziono Pythona 3.9+” | brak Pythona albo tylko atrapa z `WindowsApps` | zainstaluj Pythona 3.9+ (python.org albo Sklep Microsoft) albo załóż `.venv` w folderze narzędzia |
| „W tym oknie Power BI nie rozpoznałem pliku raportu” | nowy, niezapisany raport albo plik spoza listy ostatnich | zapisz raport (**Ctrl+S**) i kliknij **⟳**. Desktop Bridge (`npm install`) rozpoznaje plik najpewniej |
| Baner o niezapisanych zmianach | panel sprawdza wersję z dysku, a w Power BI są zmiany | **Ctrl+S**, potem **⟳** |
| „Model niedostępny” / „Raport łączy się z modelem w usłudze” | połączenie na żywo, model jeszcze się wczytuje albo brak bibliotek TOM | nic nie trzeba robić: reguły działają, oś czasu jest rozpoznawana z nazw pól (mniej trafnie). Przy wczytującym się modelu kliknij **⟳** później |
| „Zrzut wymaga Node.js i Desktop Bridge CLI” | brak Node.js albo `npm install` | zainstaluj Node.js i uruchom `npm install` w folderze narzędzia |
| „Sprawdzenie zakończyło się bez wyniku (kod N)” | analiza przerwała się bez linii `gotowe` | uruchom `analiza.ps1` ręcznie (wyżej) i sprawdź komunikat |
| „Silnik reguł zakończył się kodem 2” | silnik nie odczytał raportu (uszkodzony albo nieobsługiwany plik) | `python standardy.py --raport "<plik>"` pokaże dokładny błąd |
| „Pominięte strony podpowiedzi” | strony z małą kanwą (≤ 700×400) albo ukryte strony typu Tooltip | to zamierzone — strony podpowiedzi nie są oceniane |
| Reguła ze statusem „błąd reguły” | wyjątek w kodzie reguły | pozostałe reguły działają, a ta nie liczy się do oceny. Zgłoś problem z fragmentem `bledy_regul` z `wynik.json` |
| Panel zasłania prawe okienka Power BI (Filtry, Wizualizacje) | panel to osobne okno przyklejone do krawędzi | zwiń go do paska, przełącz na węższy albo odepnij |
| Inna ocena w panelu i w wierszu poleceń | inny wybór standardów | panel używa zapamiętanego wyboru, wiersz poleceń — `--standardy`/`--profil` (domyślnie profil Podstawowy) |

## Ograniczenia, które nie są błędami

- Reguły czytają **definicję** raportu, nie obraz: nie widzą uciętych etykiet, przewijanych tabel ani pustych
  wizualizacji. Do tego służy **Pokaż prawdziwy wygląd**.
- Liczby kategorii nie ma w definicji: przy roli Series/Legend kolory serii są brane z palety motywu dla 6 kategorii
  (waga obniżona do info, opis to zaznacza).
- Kolory z formatowania warunkowego są pomijane. Kontrast jest liczony tylko tam, gdzie tło jest znane z definicji
  (nie nad obrazem tła strony).
- Power BI Desktop nie ma API do paneli w swoim oknie, więc panel jest osobnym oknem przyklejonym do Power BI.
