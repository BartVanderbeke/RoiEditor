@echo off
echo Starting the installation of RoiEditor
cd /d "%~dp0"
python -m pip install -e . || goto :error
echo Finished the installation of RoiEditor
echo Creating shortcut on desktop
for /f "usebackq delims=" %%I in (`where pythonw.exe`) do set "PYW_PATH=%%I"

if not defined PYW_PATH (
    echo pythonw.exe not found, no shortcut created
    exit /b 1
)

powershell -NoProfile -Command ^
 "$s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'RoiEditor.lnk')); " ^
 "$s.TargetPath = '%PYW_PATH%'; " ^
 "$s.Arguments = '-m RoiEditor'; " ^
 "$s.WorkingDirectory = '%~dp0'; " ^
 "$s.IconLocation = '%~dp0RoiEditor.ico'; " ^
 "$s.Save()"


echo Added shortcut on desktop
cmd /k
exit /b

:error
echo.
echo Installation of RoiEditor failed!
exit /b