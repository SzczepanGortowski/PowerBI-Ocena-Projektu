<#
.SYNOPSIS
  Rejestruje Standardy wizualizacji jako narzędzie zewnętrzne Power BI Desktop (wstążka Narzędzia zewnętrzne).

.DESCRIPTION
  Zapisuje plik Standardy wizualizacji.pbitool.json w folderze, z którego Desktop wczytuje narzędzia przy starcie:
  %CommonProgramFiles(x86)%\Microsoft Shared\Power BI Desktop\External Tools.
  Folder należy do Program Files, więc kopiowanie wymaga zgody administratora (okno UAC).
  Plik wskazuje na uruchom.ps1 w tym folderze - po przeniesieniu repozytorium uruchom instalację ponownie.

.PARAMETER Odinstaluj
  Usuwa rejestrację.
.PARAMETER TylkoPlik
  Zapisuje plik .pbitool.json obok skryptu, bez kopiowania (np. do przekazania administratorowi).
#>
param([switch]$Odinstaluj, [switch]$TylkoPlik)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }

$wspolne = ${env:CommonProgramFiles(x86)}
if (-not $wspolne) { $wspolne = $env:CommonProgramFiles }
$cel = Join-Path $wspolne 'Microsoft Shared\Power BI Desktop\External Tools'
$nazwaPliku = 'Standardy wizualizacji.pbitool.json'
$docel = Join-Path $cel $nazwaPliku
$ps = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'

function Jako-Administrator([string]$polecenie) {
  Write-Host '  Folder narzędzi zewnętrznych wymaga uprawnień administratora - potwierdź w oknie UAC.' -ForegroundColor Yellow
  try {
    Start-Process -FilePath $ps -Verb RunAs -Wait -WindowStyle Hidden `
      -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', $polecenie)
  } catch {
    Write-Host "  Anulowano albo brak uprawnień: $($_.Exception.Message)" -ForegroundColor Red
  }
}

if ($Odinstaluj) {
  if (-not (Test-Path -LiteralPath $docel)) { Write-Host 'Narzędzie nie jest zarejestrowane.'; exit 0 }
  try { Remove-Item -LiteralPath $docel -Force } catch { Jako-Administrator "Remove-Item -LiteralPath '$docel' -Force" }
  if (Test-Path -LiteralPath $docel) { Write-Host 'Nie udało się usunąć rejestracji.' -ForegroundColor Red; exit 1 }
  Write-Host 'Usunięto. Zmiana będzie widoczna po ponownym uruchomieniu Power BI Desktop.' -ForegroundColor Green
  exit 0
}

$skrypt = Join-Path $PSScriptRoot 'uruchom.ps1'
$ikona = [Convert]::ToBase64String([IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'ikona.png')))
$definicja = [ordered]@{
  version     = '1.0.0'
  name        = 'Standardy wizualizacji'
  description = 'Kontrola raportu według wybranych standardów: WCAG, percepcja danych, IBCS, Tufte, Few, układ, spójność, dobre praktyki Microsoft (tylko odczyt)'
  path        = $ps
  arguments   = "-NoProfile -ExecutionPolicy Bypass -File `"$skrypt`" -Server `"%server%`" -Database `"%database%`""
  iconData    = "image/png;base64,$ikona"
}
$json = ConvertTo-Json -InputObject $definicja
# znaki spoza ASCII jako \uXXXX - plik jest wtedy poprawny niezależnie od tego, jak Desktop go odczyta
$json = [regex]::Replace($json, '[^\x00-\x7F]', { param($m) '\u{0:x4}' -f [int][char]$m.Value })

$tymczasowy = Join-Path $env:TEMP $nazwaPliku
[IO.File]::WriteAllText($tymczasowy, $json, (New-Object Text.UTF8Encoding $false))

if ($TylkoPlik) {
  $obok = Join-Path $PSScriptRoot $nazwaPliku
  Copy-Item -LiteralPath $tymczasowy -Destination $obok -Force
  Write-Host "Zapisano $obok - skopiuj go do: $cel" -ForegroundColor Green
  exit 0
}

try {
  New-Item -ItemType Directory -Force -Path $cel | Out-Null
  Copy-Item -LiteralPath $tymczasowy -Destination $docel -Force
} catch {
  Jako-Administrator "New-Item -ItemType Directory -Force -Path '$cel' | Out-Null; Copy-Item -LiteralPath '$tymczasowy' -Destination '$docel' -Force"
}

if (Test-Path -LiteralPath $docel) {
  Write-Host ''
  Write-Host "Zarejestrowano: $docel" -ForegroundColor Green
  Write-Host 'Uruchom ponownie Power BI Desktop - przycisk Standardy wizualizacji pojawi się na wstążce Narzędzia zewnętrzne.'
} else {
  Write-Host ''
  Write-Host 'Nie udało się zapisać rejestracji (brak zgody administratora?).' -ForegroundColor Red
  Write-Host "Alternatywa: .\instaluj.ps1 -TylkoPlik i poproś administratora o skopiowanie pliku do: $cel"
  exit 1
}
