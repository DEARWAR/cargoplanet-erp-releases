; Inno Setup script - built automatically by .github/workflows/release.yml
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{B7A1F2C4-5D3E-4A89-9C61-2E4F7D1A8B30}
AppName=Cargo Planet ERP
AppVersion={#AppVersion}
AppPublisher=Cargo Planet Nexus India Private Limited
; per-user install: no admin rights needed, so silent auto-updates just work
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\CargoPlanetERP
DisableProgramGroupPage=yes
OutputDir=installer_out
OutputBaseFilename=CargoPlanetERP-Setup
Compression=lzma2
SolidCompression=yes
CloseApplications=yes
RestartApplications=no
UninstallDisplayName=Cargo Planet ERP

[Files]
; only program files - the database lives in %APPDATA%\CargoPlanetERP and is never touched
Source: "dist\CargoPlanetERP\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autoprograms}\Cargo Planet ERP"; Filename: "{app}\CargoPlanetERP.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Cargo Planet ERP"; Filename: "{app}\CargoPlanetERP.exe"; WorkingDir: "{app}"

[Run]
; no "skipifsilent": after a silent auto-update the app re-opens by itself
Filename: "{app}\CargoPlanetERP.exe"; WorkingDir: "{app}"; Description: "Open Cargo Planet ERP"; Flags: nowait postinstall
