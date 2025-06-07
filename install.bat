@echo off
echo Starting the installation of RoiEditor
cd /d "%~dp0"
python -m pip install -e . || goto :error
echo Finished the installation of RoiEditor
echo Creating RoiEditor shortcut on desktop
for /f "usebackq delims=" %%I in (`where pythonw.exe`) do set "PYW_PATH=%%I"

if not defined PYW_PATH (
    echo pythonw.exe not found, no shortcut created for RoiEditor
    exit /b 1
)

powershell -NoProfile -Command ^
 "$s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'RoiEditor.lnk')); " ^
 "$s.TargetPath = '%PYW_PATH%'; " ^
 "$s.Arguments = '-m RoiEditor'; " ^
 "$s.WorkingDirectory = '%~dp0'; " ^
 "$s.IconLocation = '%~dp0RoiEditor.ico'; " ^
 "$s.Save()"
echo Created RoiEditor shortcut on desktop
echo Creating cellpose shortcut on desktop
for /f "usebackq delims=" %%I in (`where python.exe`) do set "PY_PATH=%%I"

if not defined PY_PATH (
    echo python.exe not found, no shortcut created for cellpose
    exit /b 1
)

where cellpose >nul 2>&1 || (echo cellpose is not yet installed && exit /b 1)
if exist "%USERPROFILE%\Desktop\cellpose.lnk" (echo cellpose shortcut already on desktop && exit /b 0)

powershell -NoProfile -Command ^
 "$s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'cellpose.lnk')); " ^
 "$s.TargetPath = '%PY_PATH%'; " ^
 "$s.Arguments = '-m cellpose'; " ^
 "$s.WorkingDirectory = '%~dp0'; " ^
 "$s.IconLocation = '%~dp0cellpose.ico'; " ^
 "$s.Save()"
echo Created cellpose shortcut on desktop
cmd /k
exit /b

:error
echo.
echo Installation of RoiEditor failed!
exit /b