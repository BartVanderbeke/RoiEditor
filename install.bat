@echo off
echo [1/3] Starting the installation of RoiEditor
cd /d "%~dp0"
python -m pip install -e . || goto :error
echo [1/3] Finished the installation of RoiEditor
echo [2/3] Creating RoiEditor shortcut on desktop
set "PYW_PATH="
for /f "delims=" %%P in ('where pythonw 2^>nul') do (
    set "PYW_PATH=%%P"
    goto :found_pythonw
)

:found_pythonw
if not defined PYW_PATH (
    echo [ERROR] Pythonw was not found. Please install Pythonw and try again
    exit /b 1
)

powershell -NoProfile -Command ^
 "$s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'RoiEditor.lnk')); " ^
 "$s.TargetPath = '%PYW_PATH%'; " ^
 "$s.Arguments = '-m RoiEditor'; " ^
 "$s.WorkingDirectory = '%~dp0'; " ^
 "$s.IconLocation = '%~dp0RoiEditor.ico'; " ^
 "$s.Save()"
echo [2/3] Created RoiEditor shortcut on desktop
set "PY_PATH="
for /f "delims=" %%P in ('where python 2^>nul') do (
    set "PY_PATH=%%P"
    goto :found_python
)
:found_python
if not defined PY_PATH (
    echo [ERROR] Python was not found. Please install Python and try again
    exit /b 1
)

where cellpose >nul 2>&1 || (echo cellpose is not yet installed && exit /b 1)
for /f "delims=" %%D in ('powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"') do (
    set "REAL_DESKTOP=%%D"
)

if exist "%REAL_DESKTOP%\cellpose.lnk" (
    echo [OK] Shortcut to cellpose already exists
    exit /b 0
) else (
    echo [INFO] Shortcut not found on desktop, will attempt to create one
)

powershell -NoProfile -Command ^
 "$s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'cellpose.lnk')); " ^
 "$s.TargetPath = '%PY_PATH%'; " ^
 "$s.Arguments = '-m cellpose'; " ^
 "$s.WorkingDirectory = '%~dp0'; " ^
 "$s.IconLocation = '%~dp0cellpose.ico'; " ^
 "$s.Save()"
echo [3/3] Created cellpose shortcut on desktop
cmd /k
exit /b

:error
echo.
echo [ERROR] Installation of RoiEditor failed!
exit /b