<#
.SYNOPSIS
  Panel Standardy wizualizacji przyklejony do okna Power BI Desktop (WebView2 + interfejs z app/).

.DESCRIPTION
  Uruchamiany ukryty przez uruchom.ps1 (przycisk na wstążce Narzędzia zewnętrzne). Odpala analiza.ps1 w tle,
  przekazuje postęp i wynik do interfejsu i zapamiętuje wybór standardów (ustawienia.json).
  Biblioteki WebView2 bierze z folderu bin Power BI Desktop (kopia w %LOCALAPPDATA%\StandardyWizualizacji\bin).
  Ponowne kliknięcie przycisku w tym samym oknie Power BI odświeża panel.
#>
param([string]$Server, [string]$Database, [int]$DesktopPid = 0)

$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\wspolne.ps1"
# postęp i wynik analizy idą przez %TEMP% (Python ze Sklepu wirtualizuje zapisy do %LOCALAPPDATA%)
$Wymiana = Join-Path $env:TEMP 'StandardyWizualizacji'
New-Item -ItemType Directory -Force -Path $Wymiana | Out-Null
$dziennik = Join-Path $Lokalne 'okno.log'
function Loguj([string]$t) { try { Add-Content -LiteralPath $dziennik -Value "$(Get-Date -Format s) $t" -Encoding UTF8 } catch { } }

$IKONY = 'ic_refresh', 'ic_double_chevrons_vertical', 'ic_chevron_right', 'ic_chevron_left', 'ic_chevron_bottom', 'ic_locked',
         'ic_unlocked', 'ic_cross', 'ic_search', 'ic_copy', 'ic_files', 'ic_camera', 'ic_notification_warning', 'ic_tick',
         'ic_quality'

try {
  Loguj "start server=$Server database=$Database pid=$DesktopPid"
  $inst = Info-Instancji $Server $DesktopPid

  # ---------------------------------------------------------------- jeden panel na okno Power BI
  $klucz = if ($inst.DesktopPid) { $inst.DesktopPid } else { 'reczny' }
  $utworzony = $false
  $muteks = New-Object Threading.Mutex($true, "Local\StandardyWizualizacji-$klucz", [ref]$utworzony)
  $sygnal = Join-Path $Lokalne "sygnal-$klucz.txt"
  if (-not $utworzony) {
    Zapisz-Tekst $sygnal "$Server|$Database"
    Loguj 'panel już działa - wysłano sygnał odświeżenia'
    exit 0
  }
  Remove-Item -LiteralPath $sygnal -ErrorAction SilentlyContinue
  Get-ChildItem -LiteralPath $Wymiana -Filter 'postep-*.jsonl' -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-1) } | Remove-Item -ErrorAction SilentlyContinue

  # ---------------------------------------------------------------- biblioteki
  Add-Type -AssemblyName System.Windows.Forms, System.Drawing
  $kopiaBin = Join-Path $Lokalne 'bin'
  New-Item -ItemType Directory -Force -Path $kopiaBin | Out-Null
  $zrodloWv = $inst.Bin
  if (-not $zrodloWv -or -not (Test-Path (Join-Path $zrodloWv 'WebView2Loader.dll'))) {
    try { $zrodloWv = Join-Path (Get-AppxPackage -Name 'Microsoft.MicrosoftPowerBIDesktop').InstallLocation 'bin' } catch { }
  }
  foreach ($f in 'Microsoft.Web.WebView2.Core.dll', 'Microsoft.Web.WebView2.WinForms.dll', 'WebView2Loader.dll') {
    $z = Join-Path $zrodloWv $f; $c = Join-Path $kopiaBin $f
    if ((Test-Path $z) -and (-not (Test-Path $c) -or (Get-Item $z).Length -ne (Get-Item $c).Length)) {
      try { Copy-Item -LiteralPath $z -Destination $c -Force } catch { }   # zajęta przez inny panel - zostaje stara kopia
    }
  }
  if (-not (Test-Path (Join-Path $kopiaBin 'WebView2Loader.dll'))) { throw 'Brak bibliotek WebView2 (folder bin Power BI Desktop).' }

  $zrodloCs = Join-Path $Narzedzie 'natywne.cs'
  $skrot = (Get-FileHash -LiteralPath $zrodloCs -Algorithm SHA1).Hash.Substring(0, 10)
  $dllNat = Join-Path $kopiaBin "StandardyNatywne-$skrot.dll"
  if (-not (Test-Path $dllNat)) {
    Add-Type -Path $zrodloCs -ReferencedAssemblies System.Windows.Forms, System.Drawing -OutputAssembly $dllNat -OutputType Library
  }
  Add-Type -Path $dllNat
  [StandardyWizualizacji.Natywne]::WlaczDpi()
  [Windows.Forms.Application]::EnableVisualStyles()
  Add-Type -Path (Join-Path $kopiaBin 'Microsoft.Web.WebView2.Core.dll')
  Add-Type -Path (Join-Path $kopiaBin 'Microsoft.Web.WebView2.WinForms.dll')
  [Microsoft.Web.WebView2.Core.CoreWebView2Environment]::SetLoaderDllFolderPath($kopiaBin)

  # ---------------------------------------------------------------- ustawienia i stan
  $plikUst = Join-Path $Lokalne 'ustawienia.json'
  $ust = @{ przypiety = $true; zwiniety = $false; szerokosc = 460; plywajace = $null; wybor = $null }
  if (Test-Path $plikUst) {
    try {
      $u = Get-Content $plikUst -Raw -Encoding UTF8 | ConvertFrom-Json
      foreach ($p in $u.PSObject.Properties) { $ust[$p.Name] = $p.Value }
    } catch { }
  }
  $ust.zwiniety = $false
  function Zapisz-Ustawienia { try { Zapisz-Tekst $plikUst (ConvertTo-Json -InputObject $ust -Compress -Depth 6) } catch { } }

  $S = @{
    hwnd = $inst.Hwnd; proces = $null; plikPostepu = $null; pozycja = 0; koniec = $true
    wynikPlik = $null; folder = $null; zrzuty = @{}; zmienia = $false; tik = 0
    desktop = $null; nazwa = ''; server = $Server; database = $Database
  }
  if ($inst.DesktopPid) { try { $S.desktop = [Diagnostics.Process]::GetProcessById([int]$inst.DesktopPid) } catch { } }
  if ($inst.Okno) { $S.nazwa = ($inst.Okno -replace '\s+[-–]\s+Power BI Desktop.*$', '' -replace '^\*', '').Trim() }

  # ---------------------------------------------------------------- okno
  $form = New-Object StandardyWizualizacji.Panel
  $form.Text = 'Standardy wizualizacji'
  $form.BackColor = [Drawing.Color]::FromArgb(0x00, 0x64, 0x20)        # kolor nagłówka - brzeg do zmiany szerokości
  $form.Padding = New-Object Windows.Forms.Padding(5, 0, 0, 0)
  $form.MinimumSize = New-Object Drawing.Size(48, 160)
  try {
    $bmp = New-Object Drawing.Bitmap (Join-Path $Narzedzie 'ikona.png')
    $form.Icon = [Drawing.Icon]::FromHandle($bmp.GetHicon())
  } catch { }

  $wv = New-Object Microsoft.Web.WebView2.WinForms.WebView2
  $wlasc = New-Object Microsoft.Web.WebView2.WinForms.CoreWebView2CreationProperties
  $wlasc.UserDataFolder = Join-Path $Lokalne 'WebView2'
  $wv.CreationProperties = $wlasc
  $wv.DefaultBackgroundColor = [Drawing.Color]::FromArgb(0xf2, 0xf2, 0xf2)
  $wv.Dock = [Windows.Forms.DockStyle]::Fill
  $form.Controls.Add($wv)

  function Wyslij([string]$json) {
    if ($wv.CoreWebView2) { try { $wv.CoreWebView2.PostWebMessageAsJson($json) } catch { Loguj "wyslij: $($_.Exception.Message)" } }
  }
  function Wyslij-Obiekt($o) { Wyslij (ConvertTo-Json -InputObject $o -Compress -Depth 6) }

  function Skala {
    if ($S.hwnd -ne [IntPtr]::Zero) { return [StandardyWizualizacji.Natywne]::Skala($S.hwnd) }
    return [StandardyWizualizacji.Natywne]::Skala($form.Handle)
  }

  function Cel-Przypiety {
    # panel przy prawej krawędzi okna Power BI, pod wstążką; zwinięty = wąski pasek niżej (miejsce na paski innych paneli)
    $h = $S.hwnd
    if ($h -eq [IntPtr]::Zero -or -not [StandardyWizualizacji.Natywne]::IsWindow($h) -or [StandardyWizualizacji.Natywne]::IsIconic($h)) { return $null }
    $r = [StandardyWizualizacji.Natywne]::Prostokat($h); $k = Skala
    $gora = $r.Top + [int](148 * $k)
    $dol = $r.Bottom - [int](30 * $k)
    if ($ust.zwiniety) {
      $sz = [int](58 * $k)
      $g = [Math]::Min($gora + [int](570 * $k), $dol - [int](200 * $k))
      return New-Object Drawing.Rectangle(($r.Right - $sz - [int](2 * $k)), $g, $sz, [Math]::Min([int](220 * $k), $dol - $g))
    }
    $sz = [Math]::Min([int]([double]$ust.szerokosc * $k), [int]($r.Width * 0.7))
    return New-Object Drawing.Rectangle(($r.Right - $sz - [int](2 * $k)), $gora, $sz, ($dol - $gora))
  }

  function Dopasuj {
    if (-not $ust.przypiety -or $S.zmienia) { return }
    $cel = Cel-Przypiety
    if ($cel -and $form.Bounds -ne $cel) { $form.Bounds = $cel }
  }

  function Zastosuj-Tryb {
    $form.TylkoLewa = [bool]$ust.przypiety
    if ($ust.przypiety) {
      $form.Padding = New-Object Windows.Forms.Padding(5, 0, 0, 0)
      Dopasuj
    } else {
      $form.Padding = New-Object Windows.Forms.Padding(5)
      $k = Skala
      $p = $ust.plywajace
      if ($p -and $p.w -gt 200) {
        $form.Bounds = New-Object Drawing.Rectangle([int]$p.x, [int]$p.y, [int]$p.w, [int]$p.h)
      } else {
        $b = $form.Bounds
        $form.Bounds = New-Object Drawing.Rectangle(($b.X - [int](40 * $k)), ($b.Y + [int](20 * $k)), [Math]::Max($b.Width, [int](460 * $k)), [Math]::Max($b.Height, [int](640 * $k)))
      }
    }
    Wyslij-Obiekt @{ typ = 'tryb'; przypiety = [bool]$ust.przypiety; zwiniety = [bool]$ust.zwiniety; szeroki = ([double]$ust.szerokosc -ge 600) }
    Zapisz-Ustawienia
  }

  # ---------------------------------------------------------------- analiza w tle
  function Analiza-Trwa { return [bool]($S.proces -and -not $S.proces.HasExited) }

  function Uruchom-Analize {
    if (Analiza-Trwa) { return }
    $S.plikPostepu = Join-Path $Wymiana ('postep-{0}-{1}.jsonl' -f $klucz, (Get-Date -Format 'HHmmssfff'))
    [IO.File]::WriteAllText($S.plikPostepu, '')
    $S.pozycja = 0; $S.koniec = $false
    $psi = New-Object Diagnostics.ProcessStartInfo
    $psi.FileName = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $argumenty = '-NoProfile -ExecutionPolicy Bypass -File "{0}" -DesktopPid {1} -Postep "{2}"' -f `
        (Join-Path $Narzedzie 'analiza.ps1'), [int]$inst.DesktopPid, $S.plikPostepu
    # pustych wartości nie przekazujemy: PowerShell 5.1 gubi argument "" i parametr zostaje bez wartości
    if ($S.server) { $argumenty += ' -Server "{0}"' -f $S.server }
    if ($S.database) { $argumenty += ' -Database "{0}"' -f $S.database }
    $psi.Arguments = $argumenty
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $S.proces = [Diagnostics.Process]::Start($psi)
    Loguj "analiza pid=$($S.proces.Id)"
    Wyslij-Obiekt @{ typ = 'analiza'; raport = $S.nazwa }
  }

  function Wyslij-Wynik {
    if (-not $S.wynikPlik -or -not (Test-Path -LiteralPath $S.wynikPlik)) { return }
    $tekst = [IO.File]::ReadAllText($S.wynikPlik, [Text.Encoding]::UTF8)
    Wyslij ('{"typ":"wynik","wynik":' + $tekst + ',"folder":' + (ConvertTo-Json -InputObject ([string]$S.folder) -Compress) + '}')
    try {
      $m = [regex]::Match($tekst, '"raport":\s*("(?:[^"\\]|\\.)*")')
      if ($m.Success) { $n = $m.Groups[1].Value | ConvertFrom-Json; $S.nazwa = $n; $form.Text = "Standardy wizualizacji - $n" }
    } catch { }
  }

  function Obsluz-Linie([string]$linia) {
    Wyslij ('{"typ":"postep","dane":' + $linia + '}')
    try { $d = $linia | ConvertFrom-Json } catch { return }
    if ($d.krok -eq 'gotowe') {
      $S.koniec = $true; $S.wynikPlik = $d.wynik; $S.folder = $d.folder
      Wyslij-Wynik
    } elseif ($d.krok -eq 'blad') {
      $S.koniec = $true
    }
  }

  function Czytaj-Postep {
    if (-not $S.plikPostepu -or $S.koniec) { return }
    $tekst = ''
    $fs = [IO.File]::Open($S.plikPostepu, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
    try {
      $dl = $fs.Length
      if ($dl -gt $S.pozycja) {
        [void]$fs.Seek($S.pozycja, [IO.SeekOrigin]::Begin)
        $n = [int]($dl - $S.pozycja)
        $bajty = New-Object byte[] $n
        $r = $fs.Read($bajty, 0, $n)
        $ost = [Array]::LastIndexOf($bajty, [byte]10, $r - 1)
        if ($ost -ge 0) { $tekst = [Text.Encoding]::UTF8.GetString($bajty, 0, $ost + 1); $S.pozycja += $ost + 1 }
      }
    } finally { $fs.Dispose() }
    foreach ($linia in ($tekst -split "`n")) { if ($linia.Trim()) { Obsluz-Linie $linia.Trim() } }
    if (-not $S.koniec -and $S.proces -and $S.proces.HasExited) {
      Start-Sleep -Milliseconds 150
      $S.koniec = $true
      Wyslij-Obiekt @{ typ = 'blad'; tekst = "Sprawdzenie zakończyło się bez wyniku (kod $($S.proces.ExitCode)). Szczegóły: $dziennik" }
    }
  }

  # ---------------------------------------------------------------- zrzut strony przez Desktop Bridge
  function Zrob-Zrzut([string]$strona) {
    $b = Bridge-Cli
    if (-not $b -or -not $inst.DesktopPid) {
      Wyslij-Obiekt @{ typ = 'zrzut'; strona = $strona; blad = 'Zrzut wymaga Node.js i Desktop Bridge CLI (npm install w folderze narzędzia).' }
      return
    }
    $plik = Join-Path $Wymiana ('zrzut-{0}-{1}.png' -f $klucz, ($strona -replace '[^\w-]', '_'))
    Remove-Item -LiteralPath $plik -ErrorAction SilentlyContinue
    $psi = New-Object Diagnostics.ProcessStartInfo
    $psi.FileName = $b.Node
    $psi.Arguments = ('"{0}" screenshot "{1}" --pid {2} --output "{3}" --scale 1 --wait-seconds 30' -f $b.Cli, $strona, [int]$inst.DesktopPid, $plik)
    $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true; $psi.RedirectStandardOutput = $true
    $S.zrzuty[$strona] = @{ proces = [Diagnostics.Process]::Start($psi); plik = $plik }
  }

  function Sprawdz-Zrzuty {
    foreach ($k in @($S.zrzuty.Keys)) {
      $z = $S.zrzuty[$k]
      if (-not $z.proces.HasExited) { continue }
      $S.zrzuty.Remove($k)
      if (Test-Path -LiteralPath $z.plik) {
        $b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($z.plik))
        Wyslij-Obiekt @{ typ = 'zrzut'; strona = $k; dane = "data:image/png;base64,$b64" }
      } else {
        $out = ''
        try { $out = $z.proces.StandardOutput.ReadToEnd() } catch { }
        $msg = 'Nie udało się zrobić zrzutu strony.'
        try { $j = $out | ConvertFrom-Json; if ($j.error.message) { $msg += ' ' + $j.error.message } } catch { }
        Wyslij-Obiekt @{ typ = 'zrzut'; strona = $k; blad = $msg }
      }
    }
  }

  # ---------------------------------------------------------------- komunikaty z panelu
  $wv.add_CoreWebView2InitializationCompleted({
    param($nadawca, $zd)
    if (-not $zd.IsSuccess) { Loguj "WebView2: $($zd.InitializationException)"; return }
    $u = $wv.CoreWebView2.Settings
    $u.AreDefaultContextMenusEnabled = $false
    $u.IsStatusBarEnabled = $false
    $u.IsZoomControlEnabled = $false
    $u.AreDevToolsEnabled = $true
    $wv.CoreWebView2.Navigate(([Uri](Join-Path $Narzedzie 'app\index.html')).AbsoluteUri)
  })

  $wv.add_WebMessageReceived({
    param($nadawca, $zd)
    try { $m = $zd.TryGetWebMessageAsString() | ConvertFrom-Json } catch { return }
    try {
      switch ($m.akcja) {
        'gotowy' {
          $ik = @{}
          $folderIkon = Join-Path $Narzedzie 'app\ikony'
          foreach ($n in $IKONY) {
            $p = Join-Path $folderIkon "$n.svg"
            if (Test-Path $p) { $ik[$n] = [IO.File]::ReadAllText($p) }
          }
          Wyslij-Obiekt @{ typ = 'start'; ikony = $ik; raport = $S.nazwa; przypiety = [bool]$ust.przypiety; zwiniety = [bool]$ust.zwiniety
                           szeroki = ([double]$ust.szerokosc -ge 600); wybor = $ust.wybor }
          if (Analiza-Trwa) { Wyslij-Obiekt @{ typ = 'analiza'; raport = $S.nazwa } }
          elseif ($S.wynikPlik) { Wyslij-Wynik }
          else { Uruchom-Analize }
        }
        'ponownie' { Uruchom-Analize }
        'wybor' { $ust.wybor = $m.wybor; Zapisz-Ustawienia }
        'zamknij' { $form.Close() }
        'przypnij' {
          if ($ust.przypiety) { $ust.przypiety = $false } else {
            $b = $form.Bounds; $ust.plywajace = @{ x = $b.X; y = $b.Y; w = $b.Width; h = $b.Height }; $ust.przypiety = $true
          }
          $ust.zwiniety = $false
          Zastosuj-Tryb
        }
        'zwin' { if ($ust.przypiety) { $ust.zwiniety = $true; Zastosuj-Tryb } }
        'rozwin' { $ust.zwiniety = $false; Zastosuj-Tryb }
        'szerzej' {
          if ([double]$ust.szerokosc -ge 600) { $ust.szerokosc = 460 } else { $ust.szerokosc = 720 }
          if (-not $ust.przypiety) {
            $k = Skala; $b = $form.Bounds; $nowa = [int]([double]$ust.szerokosc * $k)
            $form.Bounds = New-Object Drawing.Rectangle(($b.Right - $nowa), $b.Y, $nowa, $b.Height)
          }
          Zastosuj-Tryb
        }
        'kopiuj' { if ($m.tekst) { [Windows.Forms.Clipboard]::SetText([string]$m.tekst) } }
        'otworz' {
          $p = [string]$m.sciezka
          if ($p -and (Test-Path -LiteralPath $p -PathType Container)) { Start-Process -FilePath 'explorer.exe' -ArgumentList ('"{0}"' -f $p) }
          elseif ($p -and (Test-Path -LiteralPath $p)) { Start-Process -FilePath 'explorer.exe' -ArgumentList ('/select,"{0}"' -f $p) }
        }
        'przeciagnij' { [StandardyWizualizacji.Natywne]::Przeciagnij($form.Handle) }
        'zrzut' { Zrob-Zrzut ([string]$m.strona) }
      }
    } catch { Loguj "akcja $($m.akcja): $($_.Exception.Message)" }
  })

  # ---------------------------------------------------------------- zdarzenia okna i zegar
  $form.add_ResizeBegin({ $S.zmienia = $true })
  $form.add_ResizeEnd({
    $S.zmienia = $false
    if ($ust.przypiety -and -not $ust.zwiniety) { $ust.szerokosc = [int]($form.Width / (Skala)) }
    if (-not $ust.przypiety) { $b = $form.Bounds; $ust.plywajace = @{ x = $b.X; y = $b.Y; w = $b.Width; h = $b.Height } }
    Zapisz-Ustawienia
  })
  $form.add_Load({
    if ($S.hwnd -ne [IntPtr]::Zero) { [StandardyWizualizacji.Natywne]::UstawWlasciciela($form.Handle, $S.hwnd) }
    $form.TylkoLewa = [bool]$ust.przypiety
    $cel = Cel-Przypiety
    if ($ust.przypiety -and $cel) { $form.Bounds = $cel }
    else {
      $ust.przypiety = $false
      $form.Padding = New-Object Windows.Forms.Padding(5)
      $p = $ust.plywajace
      if ($p -and $p.w -gt 200) { $form.Bounds = New-Object Drawing.Rectangle([int]$p.x, [int]$p.y, [int]$p.w, [int]$p.h) }
      else { $form.Size = New-Object Drawing.Size(520, 760); $form.StartPosition = 'CenterScreen' }
    }
    [void]$wv.EnsureCoreWebView2Async()
  })

  $zegar = New-Object Windows.Forms.Timer
  $zegar.Interval = 200
  $zegar.add_Tick({
    try {
      $S.tik++
      Czytaj-Postep
      Sprawdz-Zrzuty
      Dopasuj
      if ($S.tik % 3 -eq 0 -and (Test-Path -LiteralPath $sygnal)) {
        $t = (Get-Content -LiteralPath $sygnal -Raw -Encoding UTF8)
        Remove-Item -LiteralPath $sygnal -ErrorAction SilentlyContinue
        $cz = "$t".Trim().Split('|')
        if ($cz.Count -ge 2 -and $cz[0]) { $S.server = $cz[0]; $S.database = $cz[1] }
        $ust.zwiniety = $false; Zastosuj-Tryb
        $form.Activate()
        Uruchom-Analize
      }
      if ($S.tik % 10 -eq 0 -and $S.desktop) {
        if ($S.desktop.HasExited) { $form.Close(); return }
        $S.desktop.Refresh()
        $h = $S.desktop.MainWindowHandle
        if ($h -ne [IntPtr]::Zero -and $h -ne $S.hwnd) { $S.hwnd = $h; [StandardyWizualizacji.Natywne]::UstawWlasciciela($form.Handle, $h) }
      }
    } catch { Loguj "zegar: $($_.Exception.Message)" }
  })
  $zegar.Start()

  $form.add_FormClosing({
    $zegar.Stop()
    if (Analiza-Trwa) { try { $S.proces.Kill() } catch { } }
    Zapisz-Ustawienia
  })

  [Windows.Forms.Application]::Run($form)
  try { $muteks.ReleaseMutex() } catch { }
  Loguj 'koniec'
} catch {
  Loguj "BŁĄD: $($_.Exception.Message) $($_.ScriptStackTrace)"
  try {
    Add-Type -AssemblyName System.Windows.Forms
    [void][Windows.Forms.MessageBox]::Show("Nie udało się otworzyć panelu Standardy wizualizacji:`n$($_.Exception.Message)`n`nDziennik: $dziennik", 'Standardy wizualizacji', 'OK', 'Error')
  } catch { }
  exit 1
}
