# Katalog reguł

> Plik generowany z kodu (`python docs/generuj_reguly.py`) — nie edytuj go ręcznie. Teksty reguł są w
> `standardy_wiz/reguly_<standard>.py` (dekorator `@regula`).

55 reguł w 8 standardach. Te same teksty — „dlaczego”, „jak naprawić” i źródło — panel pokazuje po rozwinięciu reguły na liście problemów.

Waga reguły: **błąd** (10 pkt), **ostrzeżenie** (4 pkt), **info** (1 pkt). Pojedyncze znalezisko może mieć wagę wyższą albo niższą niż reguła (np. kontrast poniżej 3:1 to błąd) — zob. [Ocena i konfiguracja](ocena-i-konfiguracja.md).

| Standard | Identyfikator | Reguły | W profilach |
|---|---|---|---|
| [Dostępność (WCAG 2.2 AA)](#wcag) | `wcag` | 7 | Podstawowy, Raport zarządczy (IBCS), Dostępność, Wszystkie |
| [Percepcja danych (Cleveland–McGill)](#percepcja) | `percepcja` | 8 | Podstawowy, Raport zarządczy (IBCS), Wszystkie |
| [IBCS — notacja raportów biznesowych](#ibcs) | `ibcs` | 10 | Raport zarządczy (IBCS), Wszystkie |
| [Minimalizm danych (Tufte)](#minimalizm) | `minimalizm` | 5 | Raport zarządczy (IBCS), Wszystkie |
| [Projekt dashboardu (Few)](#dashboard) | `dashboard` | 6 | Podstawowy, Wszystkie |
| [Układ i Gestalt](#uklad) | `uklad` | 7 | Podstawowy, Wszystkie |
| [Spójność raportu](#spojnosc) | `spojnosc` | 5 | Podstawowy, Raport zarządczy (IBCS), Wszystkie |
| [Dobre praktyki Power BI (Microsoft)](#microsoft) | `microsoft` | 7 | Wszystkie |

<a id="wcag"></a>

## Dostępność (WCAG 2.2 AA)

Czy raport odczyta osoba słabowidząca, z zaburzeniami widzenia barw albo z czytnikiem ekranu: kontrast tekstu i grafiki, kolory rozróżnialne przy daltonizmie, tekst alternatywny, kolejność tabulacji, rozmiar pisma.

Źródła: W3C WCAG 2.2 (SC 1.1.1, 1.4.1, 1.4.3, 1.4.11, 2.4.3, 2.4.6); Microsoft: Design Power BI reports for accessibility.

| Reguła | Co sprawdza | Waga |
|---|---|---|
| [`WCAG-01`](#wcag-01) | Kontrast tekstu (SC 1.4.3) | ostrzeżenie |
| [`WCAG-02`](#wcag-02) | Kontrast elementów graficznych (SC 1.4.11) | ostrzeżenie |
| [`WCAG-03`](#wcag-03) | Kolory serii rozróżnialne przy daltonizmie (SC 1.4.1) | ostrzeżenie |
| [`WCAG-04`](#wcag-04) | Tekst alternatywny (SC 1.1.1) | info |
| [`WCAG-05`](#wcag-05) | Minimalny rozmiar tekstu | ostrzeżenie |
| [`WCAG-06`](#wcag-06) | Kolejność tabulacji (SC 2.4.3) | info |
| [`WCAG-07`](#wcag-07) | Nazwy stron i tytuły wizualizacji (SC 2.4.6) | info |

<a id="wcag-01"></a>

### WCAG-01 · Kontrast tekstu (SC 1.4.3)

**Waga:** ostrzeżenie · **Źródło:** WCAG 2.2 SC 1.4.3 Contrast (Minimum)

**Dlaczego:** Tekst o kontraście poniżej 4,5:1 (3:1 dla tekstu ≥ 18 pt albo ≥ 14 pt pogrubionego) jest trudny do odczytania dla osób słabowidzących, na rzutniku i na ekranie w słońcu.

**Jak naprawić:** Przyciemnij tekst albo rozjaśnij tło — w motywie (textClasses, visualStyles), nie w każdej wizualizacji. Tekst na obrazie tła strony oceń na zrzucie.

<a id="wcag-02"></a>

### WCAG-02 · Kontrast elementów graficznych (SC 1.4.11)

**Waga:** ostrzeżenie · **Źródło:** WCAG 2.2 SC 1.4.11 Non-text Contrast

**Dlaczego:** Słupek, linia czy punkt o kontraście poniżej 3:1 względem tła zlewa się z tłem — trudno go zobaczyć i porównać z innymi.

**Jak naprawić:** Ciemniejszy odcień serii albo obrys. Jasne wypełnienie dopuszczalne, gdy wartość podaje etykieta danych.

<a id="wcag-03"></a>

### WCAG-03 · Kolory serii rozróżnialne przy daltonizmie (SC 1.4.1)

**Waga:** ostrzeżenie · **Źródło:** WCAG 2.2 SC 1.4.1 Use of Color; Machado, Oliveira, Fernandes 2009 (symulacja CVD)

**Dlaczego:** Około 8% mężczyzn ma zaburzenia widzenia barw. Gdy dwie serie po symulacji protanopii, deuteranopii albo tritanopii różnią się o mniej niż ΔE00 10, kolor przestaje być nośnikiem informacji.

**Jak naprawić:** Para niebieski–pomarańczowy zamiast czerwony–zielony; drugie kodowanie: etykieta przy serii, linia przerywana, znak ▲▼. Paletę motywu zmienia właściciel motywu.

<a id="wcag-04"></a>

### WCAG-04 · Tekst alternatywny (SC 1.1.1)

**Waga:** info · **Źródło:** WCAG 2.2 SC 1.1.1 Non-text Content; Microsoft: alt text w raportach Power BI

**Dlaczego:** Czytnik ekranu odczytuje tekst alternatywny zamiast wykresu — bez niego wizualizacja jest dla niego pusta.

**Jak naprawić:** Ogólne → Tekst alternatywny: jedno zdanie, co pokazuje wizualizacja (może być miarą DAX z wnioskiem).

<a id="wcag-05"></a>

### WCAG-05 · Minimalny rozmiar tekstu

**Waga:** ostrzeżenie · **Źródło:** Microsoft: Design Power BI reports for accessibility (rozmiar tekstu)

**Dlaczego:** Tekst poniżej 9 pt (12 px kanwy) na typowym ekranie ma ok. 12 px — granica czytelności; przy pomniejszeniu raportu albo na laptopie staje się nieczytelny.

**Jak naprawić:** Etykiety osi, danych, tabel i fragmentatorów ≥ 9 pt. Brakuje miejsca → mniej kategorii albo większy kafelek, nie mniejszy font.

<a id="wcag-06"></a>

### WCAG-06 · Kolejność tabulacji (SC 2.4.3)

**Waga:** info · **Źródło:** WCAG 2.2 SC 2.4.3 Focus Order; Microsoft: tab order w raportach Power BI

**Dlaczego:** Klawisz Tab i czytnik ekranu przechodzą po wizualizacjach w kolejności tabulacji. Gdy jest nieustawiona albo rozmija się z układem strony, użytkownik klawiatury skacze po stronie bez ładu.

**Jak naprawić:** Widok → Okienko Wybór → Kolejność tabulacji: od lewej do prawej, z góry na dół; elementy dekoracyjne ukryj przed tabulacją.

<a id="wcag-07"></a>

### WCAG-07 · Nazwy stron i tytuły wizualizacji (SC 2.4.6)

**Waga:** info · **Źródło:** WCAG 2.2 SC 2.4.6 Headings and Labels

**Dlaczego:** Czytnik ekranu ogłasza nazwę strony i tytuł wizualizacji — „Strona 1” albo wykres bez tytułu nie mówi, co jest dalej.

**Jak naprawić:** Nazwa strony i tytuł wizualizacji opisują treść (np. „Sprzedaż wg regionów, 2026”).

<a id="percepcja"></a>

## Percepcja danych (Cleveland–McGill)

Czy wykres koduje liczby kanałem, który oko odczytuje dokładnie (pozycja i długość zamiast kąta i pola), czy skala nie przekłamuje, czy kolory serii da się rozróżnić i czy hierarchia pisma jest czytelna.

Źródła: Cleveland i McGill 1984; Heer i Bostock 2010; Tufte 1983 (lie factor); Szafir 2018 (ΔE00).

| Reguła | Co sprawdza | Waga |
|---|---|---|
| [`PERC-01`](#perc-01) | Skuteczny kanał kodowania | info |
| [`PERC-02`](#perc-02) | Słupki i pola od zera (lie factor) | błąd |
| [`PERC-03`](#perc-03) | Bez drugiej osi wartości | ostrzeżenie |
| [`PERC-04`](#perc-04) | Najwyżej 4 miary na wykresie | ostrzeżenie |
| [`PERC-05`](#perc-05) | Kolory serii łatwe do rozróżnienia | ostrzeżenie |
| [`PERC-06`](#perc-06) | Czytelna hierarchia pisma | info |
| [`PERC-07`](#perc-07) | Najwyżej 2 kroje pisma na stronie | ostrzeżenie |
| [`PERC-08`](#perc-08) | Ta sama miara w tym samym kolorze | ostrzeżenie |

<a id="perc-01"></a>

### PERC-01 · Skuteczny kanał kodowania

**Waga:** info · **Źródło:** Cleveland i McGill 1984; Heer i Bostock 2010; Mackinlay 1986

**Dlaczego:** Pozycję i długość na wspólnej osi odczytujemy kilkukrotnie dokładniej niż kąt, pole czy nasycenie barwy — porównanie kategorii na kole albo w treemapie bywa mylące.

**Jak naprawić:** Do porównania kategorii: posortowany wykres słupkowy. Do porównania segmentów: słupki grupowane albo małe wielokrotności zamiast stosu.

<a id="perc-02"></a>

### PERC-02 · Słupki i pola od zera (lie factor)

**Waga:** błąd · **Źródło:** Tufte 1983 (lie factor); Cleveland i McGill 1984; Heer i Bostock 2010; Mackinlay 1986

**Dlaczego:** Długość słupka koduje wartość. Oś zaczynająca się powyżej zera zawyża różnice (lie factor > 1) — a przy ukrytej osi czytelnik nawet tego nie zobaczy.

**Jak naprawić:** Oś wartości słupków, pól i kaskad od 0 (valueAxis.start puste albo 0). Gdy liczą się małe różnice — wykres liniowy albo słupki odchyleń.

<a id="perc-03"></a>

### PERC-03 · Bez drugiej osi wartości

**Waga:** ostrzeżenie · **Źródło:** Few 2008 (Dual-scaled axes); Cleveland i McGill 1984; Heer i Bostock 2010; Mackinlay 1986

**Dlaczego:** Dwie skale na jednym wykresie sugerują zależność, którą tworzy wybór zakresów osi; przecięcia linii nic nie znaczą.

**Jak naprawić:** Dwa wykresy jeden pod drugim ze wspólną osią czasu albo jedna miara znormalizowana (indeks, %).

<a id="perc-04"></a>

### PERC-04 · Najwyżej 4 miary na wykresie

**Waga:** ostrzeżenie · **Źródło:** Healey 1996; Few 2006

**Dlaczego:** Każda kolejna seria to kolor do zapamiętania i dopasowania do legendy; powyżej 4 serii porównanie zamienia się w szukanie.

**Jak naprawić:** Podziel na dwa wykresy, przenieś szczegóły do tabeli albo zostaw w kolorze tylko serię wyróżnioną.

<a id="perc-05"></a>

### PERC-05 · Kolory serii łatwe do rozróżnienia

**Waga:** ostrzeżenie · **Źródło:** Sharma 2005 (CIEDE2000); Szafir 2018 (różnica barw w wizualizacji)

**Dlaczego:** Dwie serie w kolorach różniących się o mniej niż ΔE00 15 trudno rozróżnić na małych znacznikach i w legendzie.

**Jak naprawić:** Kolory serii z różnych odcieni palety; unikaj par pomarańcz–czerwień i kolorów o tej samej jasności.

<a id="perc-06"></a>

### PERC-06 · Czytelna hierarchia pisma

**Waga:** info · **Źródło:** Skale typograficzne (krok ≥ 1,15–1,2×)

**Dlaczego:** Rozmiary różniące się o mniej niż 15% wyglądają jak ten sam poziom — trzy prawie równe rozmiary (8/9/10 pt) wyglądają na przypadkowe, a zbyt wiele poziomów rozbija hierarchię.

**Jak naprawić:** Skala 3–5 poziomów (np. 28 / 14 / 12 / 10 pt) w motywie; usuń pojedyncze nadpisania fontSize.

<a id="perc-07"></a>

### PERC-07 · Najwyżej 2 kroje pisma na stronie

**Waga:** ostrzeżenie · **Źródło:** Zasady typografii użytkowej

**Dlaczego:** Każdy krój to inny „głos”; mieszanie krojów rozbija spójność i hierarchię strony.

**Jak naprawić:** Jedna rodzina (np. Segoe UI) i jej odmiany; usuń nadpisania fontFamily w wizualizacjach.

<a id="perc-08"></a>

### PERC-08 · Ta sama miara w tym samym kolorze

**Waga:** ostrzeżenie · **Źródło:** Zasada spójności kodowania (Munzner 2014)

**Dlaczego:** Gdy ta sama miara ma na dwóch wykresach strony różne kolory, czytelnik szuka różnicy, której nie ma.

**Jak naprawić:** Jawna mapa miara → kolor (Format → Kolumny/Kolory danych) i ta sama kolejność serii.

<a id="ibcs"></a>

## IBCS — notacja raportów biznesowych

International Business Communication Standards: czas w poziomie, struktura w pionie, właściwe typy wykresów, scenariusze (rok poprzedni jaśniej niż wykonanie), tytuł z komunikatem, kolor tylko z sensem, osie bez manipulacji.

Źródła: IBCS 1.2 (SAY, UNIFY, CONDENSE, CHECK, EXPRESS, SIMPLIFY, STRUCTURE).

| Reguła | Co sprawdza | Waga |
|---|---|---|
| [`IBCS-01`](#ibcs-01) | Właściwe typy wykresów (EXPRESS) | ostrzeżenie |
| [`IBCS-02`](#ibcs-02) | Czas w poziomie, struktura w pionie (UNIFY) | ostrzeżenie |
| [`IBCS-03`](#ibcs-03) | Linia tylko dla czasu i wartości ciągłych (EXPRESS) | ostrzeżenie |
| [`IBCS-04`](#ibcs-04) | Scenariusze: rok poprzedni jaśniej niż wykonanie (UNIFY) | ostrzeżenie |
| [`IBCS-05`](#ibcs-05) | Bez zbędnych elementów (SIMPLIFY) | info |
| [`IBCS-06`](#ibcs-06) | Tytuł z komunikatem (SAY) | info |
| [`IBCS-07`](#ibcs-07) | Skala bez manipulacji (CHECK) | błąd |
| [`IBCS-08`](#ibcs-08) | Kolor tylko z sensem (EXPRESS) | ostrzeżenie |
| [`IBCS-09`](#ibcs-09) | Kategorie strukturalne posortowane wg wartości (STRUCTURE) | info |
| [`IBCS-10`](#ibcs-10) | Jednolita skala dla tej samej miary (UNIFY) | ostrzeżenie |

<a id="ibcs-01"></a>

### IBCS-01 · Właściwe typy wykresów (EXPRESS)

**Waga:** ostrzeżenie · **Źródło:** IBCS 1.2 EX 1 (Replace inappropriate chart types)

**Dlaczego:** IBCS zastępuje koła, pierścienie, mierniki, lejki i treemapy wykresami słupkowymi i liniowymi — te pierwsze kodują kątem i polem, więc nie pozwalają porównać wartości.

**Jak naprawić:** Struktura → słupki poziome posortowane; udział → słupki 100% albo kaskada; wykonanie vs cel → słupki z odchyleniem.

<a id="ibcs-02"></a>

### IBCS-02 · Czas w poziomie, struktura w pionie (UNIFY)

**Waga:** ostrzeżenie · **Źródło:** IBCS 1.2 UN 3 (Unify dimensions: time horizontal, structure vertical)

**Model:** typy kolumn z modelu poprawiają trafność; bez modelu reguła rozpoznaje oś czasu z nazw pól.

**Dlaczego:** W notacji IBCS oś czasu biegnie poziomo (kolumny, linie), a kategorie strukturalne (regiony, produkty) pionowo (słupki poziome). Czas na słupkach poziomych albo w wierszach macierzy łamie tę konwencję.

**Jak naprawić:** Okresy na wykresie kolumnowym albo liniowym; w macierzy okresy w kolumnach, struktura w wierszach.

<a id="ibcs-03"></a>

### IBCS-03 · Linia tylko dla czasu i wartości ciągłych (EXPRESS)

**Waga:** ostrzeżenie · **Źródło:** IBCS 1.2 EX 2 (Use line charts for time series)

**Model:** typy kolumn z modelu poprawiają trafność; bez modelu reguła rozpoznaje oś czasu z nazw pól.

**Dlaczego:** Linia łączy punkty, więc sugeruje przebieg między nimi. Między regionami czy produktami nie ma „przebiegu” — linia na kategoriach nominalnych wprowadza w błąd.

**Jak naprawić:** Kategorie nominalne pokaż na słupkach; linię zostaw dla okresów i skal liczbowych.

<a id="ibcs-04"></a>

### IBCS-04 · Scenariusze: rok poprzedni jaśniej niż wykonanie (UNIFY)

**Waga:** ostrzeżenie · **Źródło:** IBCS 1.2 UN 1 (Unify scenarios)

**Dlaczego:** IBCS koduje scenariusze wyglądem: wykonanie (AC) ciemnoszare, rok poprzedni (PY) jasnoszare, plan (PL) kontur. Kolorowy albo ciemniejszy PY odwraca hierarchię i myli się z wykonaniem.

**Jak naprawić:** PY w jasnej szarości (np. #bfbfbf), AC ciemne; plan jako linia przerywana albo obrys.

<a id="ibcs-05"></a>

### IBCS-05 · Bez zbędnych elementów (SIMPLIFY)

**Waga:** info · **Źródło:** IBCS 1.2 SI 1–3 (Avoid cluttered layout, redundancy, decoration)

**Dlaczego:** Oś wartości obok etykiet danych, linie siatki i cienie powtarzają informację albo jej nie niosą — odciągają wzrok od liczb.

**Jak naprawić:** Przy etykietach danych wyłącz oś wartości i siatkę; usuń cienie i ozdobne ramki.

<a id="ibcs-06"></a>

### IBCS-06 · Tytuł z komunikatem (SAY)

**Waga:** info · **Źródło:** IBCS 1.2 SA 1 (Know objectives), SA 3 (Deliver message)

**Dlaczego:** IBCS zaczyna od przekazu: tytuł mówi, co z danych wynika. Tytuł automatyczny („Suma X wg Y”) albo jego brak zostawia wniosek czytelnikowi.

**Jak naprawić:** Tytuł = wniosek albo pytanie (np. „Sprzedaż rośnie w regionach wschodnich”); miara, okres i jednostka w podtytule.

<a id="ibcs-07"></a>

### IBCS-07 · Skala bez manipulacji (CHECK)

**Waga:** błąd · **Źródło:** IBCS 1.2 CH 1 (Avoid manipulated axes)

**Dlaczego:** Przycięta oś słupków albo skala logarytmiczna przy kodowaniu długością przekłamuje proporcje.

**Jak naprawić:** Oś wartości słupków od zera; małe różnice pokaż wykresem odchyleń.

<a id="ibcs-08"></a>

### IBCS-08 · Kolor tylko z sensem (EXPRESS)

**Waga:** ostrzeżenie · **Źródło:** IBCS 1.2 EX 4 (Use colors only for highlighting and signals)

**Dlaczego:** Pokolorowanie kategorii jednej serii na różne barwy nic nie znaczy, a sugeruje różnice. IBCS używa koloru do wyróżnienia i oceny (dobrze/źle), nie do dekoracji.

**Jak naprawić:** Jedna barwa dla serii; kolorem wyróżnij tylko element, o którym mówi tytuł.

<a id="ibcs-09"></a>

### IBCS-09 · Kategorie strukturalne posortowane wg wartości (STRUCTURE)

**Waga:** info · **Źródło:** IBCS 1.2 ST 3 (Use appropriate order)

**Dlaczego:** Słupki regionów czy produktów ułożone alfabetycznie każą szukać największych; posortowane wg wartości pokazują ranking od razu.

**Jak naprawić:** Sortuj malejąco po mierze (Więcej opcji → Sortuj według). Kolejność alfabetyczną zostaw dla list do wyszukiwania.

<a id="ibcs-10"></a>

### IBCS-10 · Jednolita skala dla tej samej miary (UNIFY)

**Waga:** ostrzeżenie · **Źródło:** IBCS 1.2 UN 4 (Unify scaling)

**Dlaczego:** Ta sama miara na dwóch wykresach strony z różnie ustawionym zakresem osi wygląda porównywalnie, a nie jest — równe słupki znaczą różne liczby.

**Jak naprawić:** Ten sam zakres osi (start/koniec) dla tej samej miary albo wskaźnik skali przy wykresach.

<a id="minimalizm"></a>

## Minimalizm danych (Tufte)

Mniej „atramentu” poza danymi: bez ram i cieni, bez siatki i osi dublujących etykiety danych, bez legendy przy jednej serii, bez nadmiernej precyzji.

Źródła: Tufte 1983: The Visual Display of Quantitative Information (data-ink ratio, chartjunk).

| Reguła | Co sprawdza | Waga |
|---|---|---|
| [`TUF-01`](#tuf-01) | Bez ram i cieni wokół wizualizacji | info |
| [`TUF-02`](#tuf-02) | Bez siatki przy etykietach danych | info |
| [`TUF-03`](#tuf-03) | Oś wartości albo etykiety danych — nie oba | info |
| [`TUF-04`](#tuf-04) | Legenda tylko przy kilku seriach | info |
| [`TUF-05`](#tuf-05) | Bez nadmiernej precyzji etykiet | info |

<a id="tuf-01"></a>

### TUF-01 · Bez ram i cieni wokół wizualizacji

**Waga:** info · **Źródło:** Tufte 1983: data-ink ratio, chartjunk

**Dlaczego:** Ramka i cień to atrament, który nie niesie danych — przy kilku kafelkach strona robi się ciężka, a wzrok zatrzymuje się na krawędziach zamiast na liczbach.

**Jak naprawić:** Wyłącz obramowanie i cień (Ogólne → Efekty); grupuj wizualizacje odstępem albo tłem strony.

<a id="tuf-02"></a>

### TUF-02 · Bez siatki przy etykietach danych

**Waga:** info · **Źródło:** Tufte 1983: data-ink ratio, chartjunk

**Dlaczego:** Gdy wartości podają etykiety, linie siatki nie pomagają niczego odczytać — są szumem pod danymi.

**Jak naprawić:** Wyłącz linie siatki (Oś Y → Linie siatki) albo etykiety, jeśli wykres ma służyć do odczytu z osi.

<a id="tuf-03"></a>

### TUF-03 · Oś wartości albo etykiety danych — nie oba

**Waga:** info · **Źródło:** Tufte 1983: data-ink ratio, chartjunk

**Dlaczego:** Oś wartości i etykiety danych mówią to samo; jedno z nich wystarczy (zwykle etykiety).

**Jak naprawić:** Przy etykietach danych wyłącz oś wartości — wartości czyta się z etykiet przy słupkach.

<a id="tuf-04"></a>

### TUF-04 · Legenda tylko przy kilku seriach

**Waga:** info · **Źródło:** Tufte 1983: data-ink ratio, chartjunk

**Dlaczego:** Legenda jednej serii tylko powtarza tytuł i zabiera miejsce.

**Jak naprawić:** Wyłącz legendę; nazwę serii podaj w tytule.

<a id="tuf-05"></a>

### TUF-05 · Bez nadmiernej precyzji etykiet

**Waga:** info · **Źródło:** Tufte 1983: data-ink ratio, chartjunk

**Dlaczego:** Trzy i więcej miejsc po przecinku w etykietach to cyfry, których nikt nie porównuje — utrudniają odczyt.

**Jak naprawić:** Precyzja 0–1 miejsca i jednostki wyświetlania (tys., mln) w etykietach danych.

<a id="dashboard"></a>

## Projekt dashboardu (Few)

Strona ogarnięta jednym spojrzeniem: ograniczona liczba wizualizacji i fragmentatorów, bez mierników, liczby z kontekstem (cel, rok poprzedni), mieści się na jednym ekranie.

Źródła: Few 2006: Information Dashboard Design; Miller 1956, Cowan 2001 (pamięć robocza).

| Reguła | Co sprawdza | Waga |
|---|---|---|
| [`FEW-01`](#few-01) | Najwyżej 8 wizualizacji danych na stronie | ostrzeżenie |
| [`FEW-02`](#few-02) | Najwyżej 4 fragmentatory na stronie | info |
| [`FEW-03`](#few-03) | Bez mierników (gauge) | ostrzeżenie |
| [`FEW-04`](#few-04) | Strona mieści się na jednym ekranie | info |
| [`FEW-05`](#few-05) | Liczby z kontekstem | info |
| [`FEW-06`](#few-06) | Ograniczona liczba kolorów na stronie | info |

<a id="few-01"></a>

### FEW-01 · Najwyżej 8 wizualizacji danych na stronie

**Waga:** ostrzeżenie · **Źródło:** Few 2006: Information Dashboard Design; Miller 1956, Cowan 2001

**Dlaczego:** Pamięć robocza mieści kilka elementów naraz; strona z kilkunastoma wykresami i kartami wymaga przeszukiwania zamiast spojrzenia.

**Jak naprawić:** Podziel stronę, przenieś szczegóły do drillthrough albo podpowiedzi, połącz karty w jedną kartę z wieloma wartościami.

<a id="few-02"></a>

### FEW-02 · Najwyżej 4 fragmentatory na stronie

**Waga:** info · **Źródło:** Few 2006: Information Dashboard Design

**Dlaczego:** Każdy fragmentator to decyzja do podjęcia przed odczytem; ich rząd zabiera miejsce danym.

**Jak naprawić:** Rzadko używane filtry przenieś do panelu filtrów; wspólne fragmentatory synchronizuj między stronami.

<a id="few-03"></a>

### FEW-03 · Bez mierników (gauge)

**Waga:** ostrzeżenie · **Źródło:** Few 2006: Information Dashboard Design

**Dlaczego:** Miernik zajmuje dużo miejsca, a pokazuje jedną liczbę i kąt, który trudno porównać z innymi.

**Jak naprawić:** Karta z wartością i odchyleniem od celu albo wykres pociskowy (bullet).

<a id="few-04"></a>

### FEW-04 · Strona mieści się na jednym ekranie

**Waga:** info · **Źródło:** Few 2006: Information Dashboard Design

**Dlaczego:** Dashboard ma być widoczny bez przewijania; to, co pod krawędzią ekranu, zwykle nie zostaje zauważone.

**Jak naprawić:** Kanwa 16:9 (1280×720) albo podział na strony / drillthrough zamiast wysokiej strony.

<a id="few-05"></a>

### FEW-05 · Liczby z kontekstem

**Waga:** info · **Źródło:** Few 2006: Information Dashboard Design

**Dlaczego:** Sama liczba („12 145”) nie mówi, czy to dobrze — potrzebuje porównania: cel, rok poprzedni, trend.

**Jak naprawić:** Karta z etykietą referencyjną (vs PY, vs cel) albo wizualizacja KPI z celem.

<a id="few-06"></a>

### FEW-06 · Ograniczona liczba kolorów na stronie

**Waga:** info · **Źródło:** Few 2006: Information Dashboard Design; Healey 1996

**Dlaczego:** Kilka kolorów da się odróżnić i zapamiętać; powyżej 6–8 barw kolor przestaje coś znaczyć.

**Jak naprawić:** Kolor tylko dla serii, które coś znaczą; reszta w szarości (strategia wyróżniania).

<a id="uklad"></a>

## Układ i Gestalt

Porządek na stronie: nic poza kanwą i nic na sobie, wyrównane krawędzie, rytm odstępów, równowaga, wykorzystany obszar, KPI nad szczegółami.

Źródła: Zasady Gestalt (bliskość, wyrównanie); Ngo, Teo, Byrne 2003 (miary estetyki interfejsu).

| Reguła | Co sprawdza | Waga |
|---|---|---|
| [`UKL-01`](#ukl-01) | Wizualizacje w granicach kanwy | błąd |
| [`UKL-02`](#ukl-02) | Wizualizacje nie nachodzą na siebie | ostrzeżenie |
| [`UKL-03`](#ukl-03) | Krawędzie wyrównane | info |
| [`UKL-04`](#ukl-04) | Rytm odstępów | info |
| [`UKL-05`](#ukl-05) | Równowaga strony | info |
| [`UKL-06`](#ukl-06) | Wykorzystany obszar roboczy | info |
| [`UKL-07`](#ukl-07) | KPI nad szczegółami | info |

<a id="ukl-01"></a>

### UKL-01 · Wizualizacje w granicach kanwy

**Waga:** błąd · **Źródło:** Zasady Gestalt; Ngo, Teo, Byrne 2003

**Dlaczego:** Część wizualizacji poza kanwą jest ucięta w usłudze i w aplikacji mobilnej; element cały poza kanwą jest niewidoczny, ale wciąż wykonuje zapytanie.

**Jak naprawić:** Przesuń albo zmniejsz wizualizację; element odłożony poza kanwę usuń.

<a id="ukl-02"></a>

### UKL-02 · Wizualizacje nie nachodzą na siebie

**Waga:** ostrzeżenie · **Źródło:** Zasady Gestalt; Ngo, Teo, Byrne 2003

**Dlaczego:** Nakładające się wizualizacje zasłaniają dane i przechwytują kliknięcia (filtrowanie działa na tej wyżej).

**Jak naprawić:** Rozsuń wizualizacje; świadome przełączanie widoków rób zakładkami.

<a id="ukl-03"></a>

### UKL-03 · Krawędzie wyrównane

**Waga:** info · **Źródło:** Zasady Gestalt; Ngo, Teo, Byrne 2003

**Dlaczego:** Oko łączy elementy leżące na wspólnej linii w grupę; krawędzie „prawie wyrównane” wyglądają jak błąd składu.

**Jak naprawić:** Pozycje z siatki albo z pliku towarzyszącego tła (zones[] → position); rząd kart: równe szerokości i odstępy.

<a id="ukl-04"></a>

### UKL-04 · Rytm odstępów

**Waga:** info · **Źródło:** Zasady Gestalt; Ngo, Teo, Byrne 2003

**Dlaczego:** Zasada bliskości: jeden odstęp wewnątrz grup i ewentualnie drugi, większy, między grupami. Kilka różnych odstępów rozbija grupowanie.

**Jak naprawić:** Jeden odstęp między kafelkami (np. 16 px), większy tylko między sekcjami.

<a id="ukl-05"></a>

### UKL-05 · Równowaga strony

**Waga:** info · **Źródło:** Zasady Gestalt; Ngo, Teo, Byrne 2003 (equilibrium)

**Dlaczego:** Gdy ciężar treści (pola wizualizacji) jest przesunięty do jednej krawędzi, strona wygląda na niedokończoną.

**Jak naprawić:** Rozłóż duże wizualizacje; pusta połowa strony → powiększ kafelki albo zmień układ.

<a id="ukl-06"></a>

### UKL-06 · Wykorzystany obszar roboczy

**Waga:** info · **Źródło:** Zasady Gestalt; Ngo, Teo, Byrne 2003

**Dlaczego:** Duża pusta przestrzeń przy małych wykresach marnuje ekran i zmniejsza czytelność danych.

**Jak naprawić:** Powiększ kafelki do obszaru roboczego albo zmień układ strony.

<a id="ukl-07"></a>

### UKL-07 · KPI nad szczegółami

**Waga:** info · **Źródło:** Zasady Gestalt; Ngo, Teo, Byrne 2003; Nielsen 2006 (F-pattern)

**Dlaczego:** Czytamy od góry i od lewej (skan F/Z): najważniejsze liczby powinny być pierwsze, szczegóły niżej.

**Jak naprawić:** Karty KPI w górnym rzędzie obszaru roboczego, wykresy i tabele pod nimi.

<a id="spojnosc"></a>

## Spójność raportu

Te same rzeczy wyglądają tak samo na każdej stronie: położenie fragmentatorów, kolor miary, rozmiary tytułów, kroje pisma, rozmiar stron.

Źródła: Zasada spójności (IBCS UNIFY, Few 2006).

| Reguła | Co sprawdza | Waga |
|---|---|---|
| [`SPJ-01`](#spj-01) | Fragmentatory w tym samym miejscu na każdej stronie | ostrzeżenie |
| [`SPJ-02`](#spj-02) | Jedna miara = jeden kolor w całym raporcie | ostrzeżenie |
| [`SPJ-03`](#spj-03) | Jeden rozmiar tytułów wizualizacji | info |
| [`SPJ-04`](#spj-04) | Jednakowy rozmiar stron | info |
| [`SPJ-05`](#spj-05) | Najwyżej 2 kroje pisma w raporcie | info |

<a id="spj-01"></a>

### SPJ-01 · Fragmentatory w tym samym miejscu na każdej stronie

**Waga:** ostrzeżenie · **Źródło:** Zasada spójności (IBCS UNIFY; Few 2006)

**Dlaczego:** Ten sam filtr w innym miejscu na każdej stronie każe go szukać od nowa i sugeruje, że to inny filtr.

**Jak naprawić:** Wspólne fragmentatory w stałym miejscu nagłówka (te same x, y, rozmiar), najlepiej zsynchronizowane.

<a id="spj-02"></a>

### SPJ-02 · Jedna miara = jeden kolor w całym raporcie

**Waga:** ostrzeżenie · **Źródło:** Zasada spójności (IBCS UNIFY; Few 2006)

**Dlaczego:** Gdy miara zmienia kolor między stronami, czytelnik musi za każdym razem od nowa czytać legendę.

**Jak naprawić:** Jawna mapa miara → kolor dla całego raportu (Format → Kolory danych z tym samym kolorem).

<a id="spj-03"></a>

### SPJ-03 · Jeden rozmiar tytułów wizualizacji

**Waga:** info · **Źródło:** Zasada spójności (IBCS UNIFY; Few 2006)

**Dlaczego:** Tytuły w różnych rozmiarach sugerują różną wagę wizualizacji, której zwykle nie ma.

**Jak naprawić:** Rozmiar tytułu w motywie (visualStyles.*.title.fontSize), bez nadpisań per wizualizacja.

<a id="spj-04"></a>

### SPJ-04 · Jednakowy rozmiar stron

**Waga:** info · **Źródło:** Zasada spójności (IBCS UNIFY; Few 2006)

**Dlaczego:** Strony o różnych proporcjach skaczą przy przełączaniu i inaczej skalują się na ekranie.

**Jak naprawić:** Jeden rozmiar kanwy dla stron raportu (np. 1280×720); wyjątki: strony podpowiedzi.

<a id="spj-05"></a>

### SPJ-05 · Najwyżej 2 kroje pisma w raporcie

**Waga:** info · **Źródło:** Zasada spójności (IBCS UNIFY; Few 2006)

**Dlaczego:** Różne kroje na różnych stronach sprawiają wrażenie raportu sklejonego z kilku.

**Jak naprawić:** Krój z motywu (textClasses) na wszystkich stronach; usuń nadpisania fontFamily.

<a id="microsoft"></a>

## Dobre praktyki Power BI (Microsoft)

Higiena raportu według wskazówek Microsoft: nazwy stron, liczba wizualizacji a wydajność, jawne miary, nowoczesne typy wizualizacji, wizualizacje niestandardowe, ukryte i puste elementy.

Źródła: Microsoft Learn: Power BI report design tips; Optimization guide for Power BI.

| Reguła | Co sprawdza | Waga |
|---|---|---|
| [`MS-01`](#ms-01) | Nazwy stron opisują treść | ostrzeżenie |
| [`MS-02`](#ms-02) | Liczba wizualizacji a wydajność | ostrzeżenie |
| [`MS-03`](#ms-03) | Wizualizacje niestandardowe | info |
| [`MS-04`](#ms-04) | Ukryte wizualizacje | info |
| [`MS-05`](#ms-05) | Jawne miary zamiast agregacji kolumn | ostrzeżenie |
| [`MS-06`](#ms-06) | Strony z treścią | ostrzeżenie |
| [`MS-07`](#ms-07) | Nowoczesne typy wizualizacji | info |

<a id="ms-01"></a>

### MS-01 · Nazwy stron opisują treść

**Waga:** ostrzeżenie · **Źródło:** Microsoft Learn: Power BI report design tips; Optimization guide for Power BI

**Dlaczego:** Nazwa strony to etykieta zakładki i pozycja nawigacji w aplikacji — „Strona 1” nic nie mówi odbiorcy.

**Jak naprawić:** Dwuklik na zakładce strony i nazwa mówiąca, co jest na stronie.

<a id="ms-02"></a>

### MS-02 · Liczba wizualizacji a wydajność

**Waga:** ostrzeżenie · **Źródło:** Microsoft Learn: Power BI report design tips; Optimization guide for Power BI

**Dlaczego:** Każda wizualizacja wysyła własne zapytanie przy otwarciu strony; powyżej ~15 strona ładuje się wolno.

**Jak naprawić:** Podziel stronę, użyj drillthrough i podpowiedzi, połącz karty w jedną kartę z wieloma wartościami.

<a id="ms-03"></a>

### MS-03 · Wizualizacje niestandardowe

**Waga:** info · **Źródło:** Microsoft Learn: Power BI report design tips; Optimization guide for Power BI

**Dlaczego:** Wizualizacja z AppSource zależy od licencji i aktualizacji dostawcy (np. „license expired” zamiast danych) i nie zawsze korzysta z motywu ani funkcji dostępności.

**Jak naprawić:** Natywna wizualizacja Power BI albo potwierdzona licencja organizacyjna.

<a id="ms-04"></a>

### MS-04 · Ukryte wizualizacje

**Waga:** info · **Źródło:** Microsoft Learn: Power BI report design tips; Optimization guide for Power BI

**Dlaczego:** Ukryte wizualizacje to martwy balast, chyba że przełączają je zakładki.

**Jak naprawić:** Usuń je albo opisz, którą zakładką są odsłaniane.

<a id="ms-05"></a>

### MS-05 · Jawne miary zamiast agregacji kolumn

**Waga:** ostrzeżenie · **Źródło:** Microsoft Learn: Power BI report design tips; Optimization guide for Power BI

**Dlaczego:** Niejawna miara (Suma/Średnia kolumny) nie ma formatu, opisu ani kontroli logiki, a przy grupach obliczeniowych nie działa.

**Jak naprawić:** Miara DAX w modelu (z formatem i opisem) zamiast kolumny przeciągniętej do wartości.

<a id="ms-06"></a>

### MS-06 · Strony z treścią

**Waga:** ostrzeżenie · **Źródło:** Microsoft Learn: Power BI report design tips; Optimization guide for Power BI

**Dlaczego:** Pusta strona w opublikowanym raporcie to zwykle pozostałość po pracy.

**Jak naprawić:** Usuń stronę albo ją ukryj, jeśli to szkic.

<a id="ms-07"></a>

### MS-07 · Nowoczesne typy wizualizacji

**Waga:** info · **Źródło:** Microsoft Learn: Power BI report design tips; Optimization guide for Power BI; Bing Maps retirement

**Dlaczego:** Starsze typy (karta, tabela, macierz) mają uboższe formatowanie i dostępność; mapy Bing są wycofywane.

**Jak naprawić:** Karta → nowa karta (cardVisual), tabela → tableEx, macierz → pivotTable; mapy → Azure Maps.
