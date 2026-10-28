# Instalacja

## Wymagania

| Składnik | Do czego | Obowiązkowy |
|---|---|---|
| Windows 10/11 i Power BI Desktop (ze Sklepu Microsoft albo z instalatora MSI) | przycisk na wstążce; biblioteki WebView2 (interfejs panelu) i TOM (odczyt modelu) | tak |
| Python 3.9 lub nowszy | silnik reguł — wyłącznie biblioteka standardowa, bez `pip install` | tak |
| Node.js i `npm install` w folderze narzędzia ([Desktop Bridge CLI](https://www.npmjs.com/package/@microsoft/powerbi-desktop-bridge-cli), public preview) | pewne rozpoznanie pliku otwartego w oknie Desktopa, ostrzeżenie o niezapisanych zmianach, zrzuty stron („Pokaż prawdziwy wygląd”) | nie |
| Zgoda administratora (jednorazowo, okno UAC) | zapis rejestracji przycisku w folderze Program Files | tak — albo administrator kopiuje plik za Ciebie |

Bibliotek WebView2 i TOM nie trzeba instalować: narzędzie bierze je z folderu zainstalowanego Power BI Desktop.

**Skąd narzędzie bierze Pythona** (pierwszy działający):

1. `.venv\Scripts\python.exe` w folderze narzędzia albo w jednym z trzech folderów nadrzędnych,
2. `py -3`,
3. `python` z `PATH`.

Atrapa `python.exe` z `WindowsApps`, która zamiast uruchomić Pythona otwiera Microsoft Store, jest rozpoznawana i
pomijana.

## Instalacja krok po kroku

1. **Pobierz narzędzie do stałego folderu**, np. `C:\Narzedzia\standardy-wizualizacji`. Rejestracja przycisku
   wskazuje na ten folder, więc nie trzymaj go w Pobranych.

   ```powershell
   git clone https://github.com/SzczepanGortowski/PowerBI-Ocena-Projektu.git C:\Narzedzia\standardy-wizualizacji
   cd C:\Narzedzia\standardy-wizualizacji
   ```

   Albo na GitHubie **Code → Download ZIP** i rozpakuj.

2. **Sprawdź Pythona i silnik** na raporcie demonstracyjnym:

   ```powershell
   python --version                                  # 3.9 lub nowszy
   python standardy.py --raport przyklad\Demo.Report  # powinno wypisać oceny i ścieżkę WYNIK
   ```

3. **Opcjonalnie: Desktop Bridge** — zrzuty stron i ostrzeżenie o niezapisanych zmianach:

   ```powershell
   npm install
   ```

4. **Zarejestruj przycisk** (pojawi się okno UAC):

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\instaluj.ps1
   ```

5. **Uruchom ponownie Power BI Desktop.** Przycisk **Standardy wizualizacji** pojawi się na wstążce
   **Narzędzia zewnętrzne**.

## Co robi instalator

`instaluj.ps1` zapisuje jeden plik:

```
%CommonProgramFiles(x86)%\Microsoft Shared\Power BI Desktop\External Tools\Standardy wizualizacji.pbitool.json
```

Plik mówi Desktopowi, żeby po kliknięciu przycisku uruchomił `powershell.exe -File "<folder narzędzia>\uruchom.ps1"`
z parametrami `-Server "%server%" -Database "%database%"` (adres lokalnej instancji modelu). Zawiera też ikonę
z `ikona.png` zapisaną jako base64. Instalator nie zmienia rejestru i nie instaluje usług.

## Bez uprawnień administratora

```powershell
powershell -ExecutionPolicy Bypass -File .\instaluj.ps1 -TylkoPlik
```

Skrypt zapisze `Standardy wizualizacji.pbitool.json` obok siebie. Przekaż plik administratorowi do skopiowania do
folderu `External Tools` podanego wyżej. Plik zawiera ścieżkę z Twojego komputera, dlatego jest w `.gitignore`.

## Aktualizacja

`git pull` albo podmiana plików. Ponowna instalacja **nie jest potrzebna**: przycisk uruchamia `uruchom.ps1`
z folderu narzędzia, więc zawsze działa bieżąca wersja. Uruchom `instaluj.ps1` ponownie tylko wtedy, gdy:

- przenosisz folder narzędzia w inne miejsce,
- zmieniasz `ikona.png` (ikona jest zapisana w pliku rejestracji).

## Odinstalowanie

```powershell
powershell -ExecutionPolicy Bypass -File .\instaluj.ps1 -Odinstaluj
```

Potem usuń folder narzędzia i, jeśli chcesz, pliki robocze:

- `%LOCALAPPDATA%\StandardyWizualizacji\` — ustawienia panelu, dziennik, kopia bibliotek WebView2, profil przeglądarki panelu,
- `%TEMP%\StandardyWizualizacji\` — wyniki sprawdzeń i pliki wymiany.
