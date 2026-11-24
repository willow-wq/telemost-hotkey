$ErrorActionPreference = 'Stop'
$helperPath = Join-Path $PSScriptRoot 'telemost_hotkey.pyw'
$shortcutPath = Join-Path ([Environment]::GetFolderPath('Startup')) 'Telemost Right Shift Mic.lnk'
if (Test-Path -LiteralPath $shortcutPath) {
    $shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut($shortcutPath)
    if ($shortcut.Arguments -match ([regex]::Escape($helperPath) + '(?:"|\s|$)')) {
        Remove-Item -LiteralPath $shortcutPath
    } else {
        Write-Warning 'The startup shortcut points elsewhere; it was left unchanged.'
    }
}
$helperPattern = [regex]::Escape($helperPath) + '(?:"|\s|$)'
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" |
    Where-Object { $_.CommandLine -and $_.CommandLine -match $helperPattern } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }
Write-Output 'Removed this copy from startup and stopped its processes. Source files and logs were kept.'

