# Wspólne funkcje panelu (okno.ps1) i analizy (analiza.ps1). Dot-source: . "$PSScriptRoot\wspolne.ps1"

$Narzedzie = $PSScriptRoot
$Lokalne = Join-Path $env:LOCALAPPDATA 'StandardyWizualizacji'
New-Item -ItemType Directory -Force -Path $Lokalne | Out-Null

function Zapisz-Tekst([string]$sciezka, [string]$tekst) {
  [IO.File]::WriteAllText($sciezka, $tekst, (New-Object Text.UTF8Encoding $false))
}

function Znajdz-W-Gore([string]$wzgledna, [int]$poziomy = 3) {
  # plik w folderze narzędzia albo w folderach nadrzędnych (np. .venv i node_modules repozytorium, w którym leży narzędzie)
  $folder = $Narzedzie
  for ($i = 0; $i -le $poziomy -and $folder; $i++) {
    $p = Join-Path $folder $wzgledna
    if (Test-Path -LiteralPath $p) { return $p }
    $folder = Split-Path $folder -Parent
  }
  return $null
}

function Znajdz-Pythona {
  # .venv obok narzędzia (albo w repozytorium wyżej), potem launcher py i python z PATH
  $venv = Znajdz-W-Gore '.venv\Scripts\python.exe'
  if ($venv) { return , @($venv) }
  foreach ($kand in @(@('py', '-3'), @('python'))) {
    $c = Get-Command $kand[0] -ErrorAction SilentlyContinue
    if (-not $c) { continue }
    $arg = @(); if ($kand.Count -gt 1) { $arg = $kand[1..($kand.Count - 1)] }
    try {
      # python z WindowsApps bywa atrapą otwierającą Microsoft Store - sprawdzamy, czy naprawdę działa
      $v = & $c.Source @arg -c 'import sys; print(sys.version_info[0] * 100 + sys.version_info[1])' 2>$null
      if ([int]"$v" -ge 309) { return , @(@($c.Source) + $arg) }
    } catch { }
  }
  return $null
}

function Info-Instancji([string]$serwer, [int]$procesDesktopa = 0) {
  # Desktop przekazuje localhost:<port> lokalnej instancji Analysis Services;
  # port -> msmdsrv.exe -> proces nadrzędny PBIDesktop.exe (ścieżka bibliotek, linia poleceń, okno)
  $wynik = [ordered]@{ Port = $null; Bin = $null; DesktopPid = $null; Linia = $null; Okno = $null; Hwnd = [IntPtr]::Zero; Serwer = $null }
  $msPid = $null
  if ($serwer -match ':(\d+)$') {
    $wynik.Port = [int]$Matches[1]
    try {
      $c = Get-NetTCPConnection -LocalPort $wynik.Port -State Listen -ErrorAction Stop | Select-Object -First 1
      $msPid = $c.OwningProcess
    } catch {
      $linia = netstat -ano | Select-String -Pattern "[:.]$($wynik.Port)\s+\S+\s+LISTENING\s+(\d+)" | Select-Object -First 1
      if ($linia) { $msPid = [int]$linia.Matches[0].Groups[1].Value }
    }
  }
  if ($msPid) {
    $ms = Get-CimInstance Win32_Process -Filter "ProcessId=$msPid"
    if ($ms) {
      $wynik.Bin = Split-Path $ms.ExecutablePath
      if (-not $procesDesktopa) { $procesDesktopa = $ms.ParentProcessId }
    }
  }
  if (-not $procesDesktopa) {
    $wszystkie = @(Get-CimInstance Win32_Process -Filter "Name='PBIDesktop.exe'")
    if ($wszystkie.Count -eq 1) { $procesDesktopa = $wszystkie[0].ProcessId }
  }
  if ($procesDesktopa) {
    $cim = Get-CimInstance Win32_Process -Filter "ProcessId=$procesDesktopa"
    if ($cim) { $wynik.DesktopPid = $cim.ProcessId; $wynik.Linia = $cim.CommandLine }
    $proc = Get-Process -Id $procesDesktopa -ErrorAction SilentlyContinue
    if ($proc) {
      $wynik.Okno = $proc.MainWindowTitle
      $wynik.Hwnd = $proc.MainWindowHandle
      if (-not $wynik.Bin -and $proc.Path) { $wynik.Bin = Split-Path $proc.Path }
    }
  }
  # bez %server% (kliknięcie w trakcie wczytywania pliku): port z msmdsrv należącego do tego okna
  $wynik.Serwer = $serwer
  if (-not $serwer -and $wynik.DesktopPid) {
    $ms = Get-CimInstance Win32_Process -Filter "Name='msmdsrv.exe'" | Where-Object { $_.ParentProcessId -eq $wynik.DesktopPid } | Select-Object -First 1
    if ($ms) {
      try {
        $c = Get-NetTCPConnection -OwningProcess $ms.ProcessId -State Listen -ErrorAction Stop | Select-Object -First 1
        if ($c) { $wynik.Serwer = "localhost:$($c.LocalPort)"; $wynik.Port = $c.LocalPort; if (-not $wynik.Bin) { $wynik.Bin = Split-Path $ms.ExecutablePath } }
      } catch { }
    }
  }
  if (-not $wynik.Bin) {
    try { $wynik.Bin = Join-Path (Get-AppxPackage -Name 'Microsoft.MicrosoftPowerBIDesktop').InstallLocation 'bin' } catch { }
  }
  return [pscustomobject]$wynik
}

function Plik-Z-Linii([string]$linia) {
  if (-not $linia) { return $null }
  foreach ($m in [regex]::Matches($linia, '"([^"]+\.(?:pbix|pbip|pbit))"|(\S+\.(?:pbix|pbip|pbit))', 'IgnoreCase')) {
    $p = if ($m.Groups[1].Success) { $m.Groups[1].Value } else { $m.Groups[2].Value }
    if (Test-Path -LiteralPath $p) { return $p }
  }
  return $null
}

function Plik-Z-Ostatnich([string]$okno) {
  # Desktop trzyma listę ostatnich plików w User.zip -> UserInterface/Settings.xml
  $nazwa = ($okno -replace '\s+[-–]\s+Power BI Desktop.*$', '' -replace '^\*|\*$', '').Trim()
  if (-not $nazwa) { return $null }
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $zipy = @("$env:USERPROFILE\Microsoft\Power BI Desktop Store App\User.zip",
            "$env:USERPROFILE\Microsoft\Power BI Desktop\User.zip",
            "$env:LOCALAPPDATA\Microsoft\Power BI Desktop\User.zip")
  foreach ($z in $zipy) {
    if (-not (Test-Path -LiteralPath $z)) { continue }
    try {
      $kopia = Join-Path $env:TEMP ("standardy-user-" + [guid]::NewGuid() + '.zip')
      Copy-Item -LiteralPath $z -Destination $kopia
      $arch = [IO.Compression.ZipFile]::OpenRead($kopia)
      try {
        $wpis = $arch.Entries | Where-Object { $_.FullName -eq 'UserInterface/Settings.xml' } | Select-Object -First 1
        if (-not $wpis) { continue }
        $sr = New-Object IO.StreamReader($wpis.Open()); $tekst = $sr.ReadToEnd(); $sr.Close()
      } finally { $arch.Dispose(); Remove-Item -LiteralPath $kopia -ErrorAction SilentlyContinue }
      foreach ($m in [regex]::Matches($tekst, '[A-Za-z]:\\\\[^"<>|]*?\.(?:pbix|pbip|pbit)', 'IgnoreCase')) {
        $p = $m.Value -replace '\\\\', '\'
        if ([IO.Path]::GetFileNameWithoutExtension($p) -eq $nazwa -and (Test-Path -LiteralPath $p)) { return $p }
      }
    } catch { }
  }
  return $null
}

function Bridge-Cli {
  # Desktop Bridge CLI (@microsoft/powerbi-desktop-bridge-cli): npm install obok narzędzia, w repozytorium wyżej albo globalnie
  $node = Get-Command node -ErrorAction SilentlyContinue
  if (-not $node) { return $null }
  $wzgl = 'node_modules\@microsoft\powerbi-desktop-bridge-cli\dist\index.js'
  $cli = Znajdz-W-Gore $wzgl
  if (-not $cli -and $env:APPDATA -and (Test-Path -LiteralPath (Join-Path $env:APPDATA "npm\$wzgl"))) { $cli = Join-Path $env:APPDATA "npm\$wzgl" }
  if (-not $cli) { return $null }
  return [pscustomobject]@{ Node = $node.Source; Cli = $cli }
}

function Stan-Bridge([int]$procesDesktopa, [int]$czekajS = 2) {
  # Desktop Bridge (potok pbi-desktop-bridge-<pid>): bieżący plik i niezapisane zmiany
  $b = Bridge-Cli
  if (-not $b -or -not $procesDesktopa) { return $null }
  try {
    $tekst = (& $b.Node $b.Cli status --pid $procesDesktopa --wait-seconds $czekajS 2>$null) -join "`n"
    $j = $tekst | ConvertFrom-Json
    $i = @($j.instances) | Select-Object -First 1
    if ($i -and $i.bridgeStatus -eq 'connected') {
      return [pscustomobject]@{ Plik = "$($i.currentFilePath)"; Niezapisane = [bool]$i.hasUnsavedChanges }
    }
  } catch { }
  return $null
}

function Czy-Model-Lokalny([string]$plik) {
  # .pbix z DataModel albo .pbip z datasetReference.byPath = model lokalny w Desktopie;
  # w przeciwnym razie raport łączy się na żywo z modelem w usłudze
  if (-not $plik) { return $null }
  try {
    if ($plik -match '\.pbi[xt]$') {
      Add-Type -AssemblyName System.IO.Compression.FileSystem
      $z = [IO.Compression.ZipFile]::OpenRead($plik)
      try { return [bool]($z.Entries | Where-Object { $_.FullName -eq 'DataModel' } | Select-Object -First 1) } finally { $z.Dispose() }
    }
    if ($plik -match '\.pbip$') {
      $p = Get-Content -LiteralPath $plik -Raw -Encoding UTF8 | ConvertFrom-Json
      $rel = ($p.artifacts | Where-Object { $_.report } | Select-Object -First 1).report.path
      $def = Join-Path (Split-Path $plik) (Join-Path $rel 'definition.pbir')
      if (Test-Path -LiteralPath $def) {
        $d = Get-Content -LiteralPath $def -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($d.datasetReference.byConnection) { return $false }
        return $true
      }
    }
  } catch { }
  return $null
}
