<#
.SYNOPSIS
  Sprawdzenie raportu otwartego w Power BI Desktop według standardów wizualizacji (wywołuje je panel okno.ps1).

.DESCRIPTION
  1. rozpoznaje plik raportu: Desktop Bridge (bieżący plik, niezapisane zmiany), linia poleceń Desktopa,
     lista ostatnich plików,
  2. opcjonalnie czyta model przez TOM (tylko definicja: typy kolumn poprawiają rozpoznanie osi czasu;
     bez zapytań DAX),
  3. uruchamia silnik standardy.py -> wynik.json (wszystkie reguły; wybór standardów robi panel).
  Postęp zapisuje jako linie JSON do pliku -Postep. Niczego nie zmienia w modelu ani w raporcie.

.EXAMPLE
  powershell -File analiza.ps1 -DesktopPid 12345
  powershell -File analiza.ps1 -Raport "C:\raporty\Sprzedaz.pbip"
#>
param(
  [string]$Server,
  [string]$Database,
  [string]$Raport,
  [int]$DesktopPid = 0,
  [string]$Postep,
  [string]$Wyjscie,
  [int]$CzekajNaModelS = 60
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
. "$PSScriptRoot\wspolne.ps1"
# wymiana plików przez %TEMP%: Python ze Sklepu Microsoft zapisuje %LOCALAPPDATA% w prywatnym folderze pakietu
$Wymiana = Join-Path $env:TEMP 'StandardyWizualizacji'
New-Item -ItemType Directory -Force -Path $Wymiana | Out-Null

function Postep([string]$krok, [string]$stan, [string]$tekst, $proc = $null, [hashtable]$dodatkowe = $null) {
  Write-Host "[$krok] $tekst"
  if (-not $Postep) { return }
  $o = [ordered]@{ krok = $krok; stan = $stan; tekst = $tekst; czas = (Get-Date -Format 'HH:mm:ss') }
  if ($null -ne $proc) { $o.proc = $proc }
  if ($dodatkowe) { foreach ($k in $dodatkowe.Keys) { $o[$k] = $dodatkowe[$k] } }
  [IO.File]::AppendAllText($Postep, ((ConvertTo-Json -InputObject $o -Compress -Depth 4) + "`n"), (New-Object Text.UTF8Encoding $false))
}
function Zakoncz-Bledem([string]$t) {
  Postep 'blad' 'blad' $t
  exit 1
}

try {
  $python = Znajdz-Pythona
  if (-not $python) { Zakoncz-Bledem 'Nie znaleziono Pythona 3.9+ (.venv obok narzędzia albo w repozytorium wyżej, py ani python).' }

  # ---------------------------------------------------------------- raport
  Postep 'raport' 'trwa' 'Rozpoznaję otwarty raport'
  $inst = Info-Instancji $Server $DesktopPid
  if (-not $Server -and $inst.Serwer) { $Server = $inst.Serwer }
  $bridge = Stan-Bridge $inst.DesktopPid 3
  if (-not $Raport -and $bridge -and $bridge.Plik -and (Test-Path -LiteralPath $bridge.Plik)) { $Raport = $bridge.Plik }
  if (-not $Raport) { $Raport = Plik-Z-Linii $inst.Linia }
  if (-not $Raport -and $inst.Okno) { $Raport = Plik-Z-Ostatnich $inst.Okno }
  if (-not $Raport -and $inst.DesktopPid) {
    # plik dopiero się wczytuje (okno Bez tytułu): bridge poda go po wczytaniu
    $start = [Diagnostics.Stopwatch]::StartNew()
    while (-not $Raport -and $start.Elapsed.TotalSeconds -lt 30) {
      Postep 'raport' 'trwa' ("Power BI wczytuje plik… ({0} s)" -f [int]$start.Elapsed.TotalSeconds)
      Start-Sleep -Seconds 2
      $b2 = Stan-Bridge $inst.DesktopPid 1
      if ($b2 -and $b2.Plik -and (Test-Path -LiteralPath $b2.Plik)) { $bridge = $b2; $Raport = $b2.Plik }
    }
  }
  if (-not $Raport) {
    Zakoncz-Bledem 'W tym oknie Power BI nie rozpoznałem pliku raportu (nowy, niezapisany raport?). Zapisz raport (Ctrl+S) i kliknij odśwież.'
  }
  # flaga dotyczy pliku otwartego w tym oknie - nie raportu podanego ręcznie (-Raport), gdy w oknie jest inny plik
  $niezapisane = [bool]($bridge -and $bridge.Niezapisane -and $bridge.Plik -and
                        [IO.Path]::GetFullPath($bridge.Plik) -eq [IO.Path]::GetFullPath($Raport))
  $zapis = (Get-Item -LiteralPath $Raport).LastWriteTime.ToString('HH:mm dd.MM')
  $opis = [IO.Path]::GetFileName($Raport)
  if ($niezapisane) { Postep 'raport' 'uwaga' "$opis - niezapisane zmiany; sprawdzam wersję z dysku ($zapis)" }
  else { Postep 'raport' 'ok' "$opis (zapisany $zapis)" }

  $nazwa = ([IO.Path]::GetFileNameWithoutExtension($Raport) -replace '[^\w .\-]', '_').Trim()
  if (-not $Wyjscie) { $Wyjscie = Join-Path $Wymiana $nazwa }
  New-Item -ItemType Directory -Force -Path $Wyjscie | Out-Null
  $klucz = if ($inst.DesktopPid) { $inst.DesktopPid } else { 'reczny' }

  # ---------------------------------------------------------------- model (opcjonalnie, tylko definicja)
  $argsModel = @()
  $statusModelu = 'brak'
  $modelLokalny = Czy-Model-Lokalny $Raport
  if ($Server -and $modelLokalny -ne $false) {
    Postep 'model' 'trwa' 'Czytam definicję modelu (typy kolumn - rozpoznanie osi czasu)'
    try {
      $bin = $inst.Bin
      if (-not $bin -or -not (Test-Path (Join-Path $bin 'Microsoft.AnalysisServices.Server.Tabular.dll'))) { throw 'brak bibliotek TOM w folderze Power BI Desktop' }
      try {
        Add-Type -Path (Join-Path $bin 'Microsoft.AnalysisServices.Server.Core.dll')
        Add-Type -Path (Join-Path $bin 'Microsoft.AnalysisServices.Server.Tabular.dll')
      } catch { }
      $start = [Diagnostics.Stopwatch]::StartNew()
      $db = $null; $srv = $null
      while ($true) {
        try {
          $srv = New-Object Microsoft.AnalysisServices.Tabular.Server
          $srv.Connect("Data Source=$Server")
          $bazy = @($srv.Databases)
          $db = $bazy | Where-Object { $_.Name -eq $Database -or $_.ID -eq $Database } | Select-Object -First 1
          $najw = $bazy | Sort-Object { $_.Model.Tables.Count } -Descending | Select-Object -First 1
          if (-not $db -or ($db.Model.Tables.Count -eq 0 -and $najw -and $najw.Model.Tables.Count -gt 0)) { $db = $najw }
        } catch { $db = $null }
        if ($db -and $db.Model.Tables.Count -gt 0) { break }
        if ($start.Elapsed.TotalSeconds -ge $CzekajNaModelS -or $modelLokalny -ne $true) { break }
        Postep 'model' 'trwa' ("Power BI jeszcze wczytuje model… ({0} s)" -f [int]$start.Elapsed.TotalSeconds)
        if ($srv) { try { $srv.Disconnect() } catch { } }
        Start-Sleep -Seconds 2
      }
      if ($db -and $db.Model.Tables.Count -gt 0) {
        $plikModelu = Join-Path $Wymiana "model-$klucz.json"
        Zapisz-Tekst $plikModelu ([Microsoft.AnalysisServices.Tabular.JsonSerializer]::SerializeDatabase($db))
        $argsModel = @('--model', $plikModelu)
        $statusModelu = 'ok'
        Postep 'model' 'ok' "$($db.Model.Tables.Count) tabel - typy kolumn wczytane"
      } else {
        Postep 'model' 'pominiety' 'Model niedostępny (wczytuje się albo połączenie na żywo) - oś czasu rozpoznam z nazw pól'
      }
      if ($srv) { try { $srv.Disconnect() } catch { } }
    } catch {
      Postep 'model' 'pominiety' "Bez modelu ($($_.Exception.Message)) - oś czasu rozpoznam z nazw pól"
    }
  } elseif ($modelLokalny -eq $false) {
    Postep 'model' 'pominiety' 'Raport łączy się z modelem w usłudze - oś czasu rozpoznam z nazw pól'
  } else {
    Postep 'model' 'pominiety' 'Bez połączenia z Desktopem - oś czasu rozpoznam z nazw pól'
  }

  # ---------------------------------------------------------------- reguły
  Postep 'reguly' 'trwa' 'Sprawdzam standardy wizualizacji'
  $desktop = [ordered]@{ pid = $inst.DesktopPid; okno = $inst.Okno; serwer = $Server; plik = $Raport; niezapisane = $niezapisane;
                         model = $statusModelu; bridge = [bool]$bridge }
  $plikDesktop = Join-Path $Wymiana "desktop-$klucz.json"
  Zapisz-Tekst $plikDesktop (ConvertTo-Json -InputObject $desktop -Compress)
  $opisZrodla = 'uruchomienie ręczne'
  if ($inst.DesktopPid) { $opisZrodla = "Power BI Desktop (PID $($inst.DesktopPid))"; if ($inst.Okno) { $opisZrodla += " - okno: $($inst.Okno)" } }
  $argsPy = @()
  if ($python.Count -gt 1) { $argsPy += $python[1..($python.Count - 1)] }
  $argsPy += @('-X', 'utf8', (Join-Path $Narzedzie 'standardy.py'), '--raport', $Raport, '--wyjscie', $Wyjscie,
               '--desktop', $plikDesktop, '--zrodlo', $opisZrodla)
  $argsPy += $argsModel
  $env:PYTHONIOENCODING = 'utf-8'
  $wyjscieTekst = & $python[0] @argsPy 2>&1
  $kod = $LASTEXITCODE
  $wynik = $null
  foreach ($l in $wyjscieTekst) {
    $s = "$l"
    if ($s -like 'WYNIK: *') { $wynik = $s.Substring(7).Trim() } else { Write-Host "  $s" }
  }
  if ($kod -ne 0 -or -not $wynik) {
    Zakoncz-Bledem ("Silnik reguł zakończył się kodem $kod. " + (($wyjscieTekst | Select-Object -Last 3) -join ' '))
  }
  Postep 'reguly' 'ok' 'Standardy sprawdzone'
  Postep 'gotowe' 'ok' 'Gotowe' 100 @{ wynik = $wynik; folder = $Wyjscie }
} catch {
  Zakoncz-Bledem ('Nieoczekiwany błąd: ' + $_.Exception.Message)
}
