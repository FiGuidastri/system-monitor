[Setup]
AppName=Monitor de Programas
AppVersion=1.0
DefaultDirName={autopf}\MonitorProgramas
DefaultGroupName=MonitorProgramas
OutputDir=.
OutputBaseFilename=MonitorSetup

[Files]
Source: "dist\monitor.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "monitor.bat"; DestDir: "{app}"; Flags: ignoreversion

[Run]
Filename: "{app}\monitor.bat"; Description: "Iniciar Monitor"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "MonitorProgramas"; ValueData: """{app}\monitor.bat"""
