#define AppName "Telemost Right Shift Mic"
#define AppVersion "0.1.0"
[Setup]
AppId={{A5FA44E7-25D6-45E0-9072-B90B359F014C}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\TelemostHotkey
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\..\output
OutputBaseFilename=TelemostHotkey-Setup-0.1.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\TelemostHotkey.exe
CloseApplications=no
InfoBeforeFile=installer-info.txt
[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
[Tasks]
Name: "autostart"; Description: "Запускать автоматически при входе в Windows"
[Files]
Source: "dist\TelemostHotkey.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{userstartup}\Telemost Right Shift Mic"; Filename: "{app}\TelemostHotkey.exe"; Parameters: "--watch"; Tasks: autostart
Name: "{group}\Telemost Right Shift Mic"; Filename: "{app}\TelemostHotkey.exe"; Parameters: "--watch"
Name: "{group}\Удалить Telemost Right Shift Mic"; Filename: "{uninstallexe}"
[Run]
Filename: "{app}\TelemostHotkey.exe"; Parameters: "--watch"; Flags: nowait runhidden skipifsilent
[UninstallRun]
Filename: "{app}\TelemostHotkey.exe"; Parameters: "--stop"; Flags: runhidden waituntilterminated; RunOnceId: "StopHelper"
[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var ResultCode: Integer;
begin
  Result := '';
  if FileExists(ExpandConstant('{app}\TelemostHotkey.exe')) then
    if not Exec(ExpandConstant('{app}\TelemostHotkey.exe'), '--stop', '', SW_HIDE,
      ewWaitUntilTerminated, ResultCode) then
      Result := 'Не удалось остановить предыдущую версию утилиты.'
    else if ResultCode <> 0 then
      Result := 'Предыдущая версия ещё работает. Завершите её и повторите установку.';
end;
