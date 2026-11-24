param([string]$PythonPath)

$ErrorActionPreference = 'Stop'
$helperPath = Join-Path $PSScriptRoot 'telemost_hotkey.pyw'
if (-not (Test-Path -LiteralPath $helperPath)) {
    throw 'telemost_hotkey.pyw was not found beside this installer.'
}
if (-not $PythonPath) {
    $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue |
        Where-Object { $_.Source -notmatch '\\WindowsApps\\' } |
        Select-Object -First 1
    if (-not $pythonCommand) {
        throw 'Python was not found. Install Python 3.10+ or pass -PythonPath with the full path to python.exe.'
    }
    $PythonPath = $pythonCommand.Source
}
$PythonPath = (Resolve-Path -LiteralPath $PythonPath).Path
& $PythonPath -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.10 or newer is required.' }
$pythonwPath = Join-Path (Split-Path -LiteralPath $PythonPath) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonwPath)) {
    throw 'pythonw.exe was not found beside the selected Python executable.'
}
$shortcutPath = Join-Path ([Environment]::GetFolderPath('Startup')) 'Telemost Right Shift Mic.lnk'
$shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pythonwPath
$shortcut.Arguments = '"' + $helperPath + '" --watch'
$shortcut.WorkingDirectory = $PSScriptRoot
$shortcut.WindowStyle = 7
$shortcut.Description = 'Right Shift microphone toggle during Yandex Telemost calls'
$shortcut.Save()
Start-Process -FilePath $pythonwPath -ArgumentList ('"' + $helperPath + '" --watch') -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
Write-Output 'Installed for the current Windows user and started. Keep this folder in its current location.'

