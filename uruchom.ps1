<#
.SYNOPSIS
  Starter przycisku Standardy wizualizacji w Power BI Desktop (Narzędzia zewnętrzne).

.DESCRIPTION
  Desktop wywołuje ten plik z -Server "%server%" -Database "%database%" (patrz instaluj.ps1).
  Starter odpala panel okno.ps1 jako osobny, ukryty proces i od razu się kończy. Proces nadrzędny
  to okno Power BI, z którego kliknięto przycisk - panel przykleja się właśnie do niego.

  Celowo bez bloku param(): PowerShell 5.1 gubi pusty argument "" z linii poleceń (-Database ""
  przy raporcie z połączeniem na żywo albo przy kliknięciu w trakcie wczytywania pliku), a wtedy
  parametr nazwany kończy się błędem Missing an argument.
#>

$Server = ''; $Database = ''
for ($i = 0; $i -lt $args.Count; $i++) {
  $a = [string]$args[$i]
  $nast = if ($i + 1 -lt $args.Count) { [string]$args[$i + 1] } else { '' }
  if ($a -match '^-Server:?(.*)$') { if ($Matches[1]) { $Server = $Matches[1] } elseif ($nast -notlike '-*') { $Server = $nast; $i++ } }
  elseif ($a -match '^-Database:?(.*)$') { if ($Matches[1]) { $Database = $Matches[1] } elseif ($nast -notlike '-*') { $Database = $nast; $i++ } }
}

$desktopPid = 0
try {
  $ja = Get-CimInstance Win32_Process -Filter "ProcessId=$PID"
  $rodzic = Get-CimInstance Win32_Process -Filter "ProcessId=$($ja.ParentProcessId)"
  if ($rodzic -and $rodzic.Name -match '^PBIDesktop') { $desktopPid = [int]$rodzic.ProcessId }
} catch { }

$argumenty = '-NoProfile -STA -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}" -DesktopPid {1}' -f (Join-Path $PSScriptRoot 'okno.ps1'), $desktopPid
if ($Server) { $argumenty += ' -Server "{0}"' -f $Server }
if ($Database) { $argumenty += ' -Database "{0}"' -f $Database }
Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe') -ArgumentList $argumenty -WindowStyle Hidden
