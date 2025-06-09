@echo off
setlocal

echo [1/3] Searching for python.exe
set "PY_PATH="
for /f "delims=" %%P in ('where python 2^>nul') do (
    set "PY_PATH=%%P"
    goto :found_python
)

:found_python
if not defined PY_PATH (
    echo [ERROR] Python was not found. Please install Python and try again.
    exit /b 1
)

echo [OK] Python found: %PY_PATH%

echo.
echo [2/3] Installing cellpose
python -m pip install --upgrade pip >nul 2>&1
python -m pip install cellpose[gui]
if errorlevel 1 (
    echo [ERROR] Failed to install Cellpose.
    exit /b 1
)
echo [OK] cellpose successfully installed

echo.
echo [3/3] Creating desktop shortcut for cellpose
set "ICO=%~dp0assets\cellpose.ico"
powershell -NoProfile -Command ^
 "$s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'cellpose.lnk')); " ^
 "$s.TargetPath = 'python.exe'; " ^
 "$s.Arguments = '-m cellpose'; " ^
 "$s.WorkingDirectory = $env:USERPROFILE; " ^
 "$s.IconLocation = '%ICO%'; " ^
 "$s.Save()"

for /f "delims=" %%D in ('powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"') do (
    set "REAL_DESKTOP=%%D"
)

if exist "%REAL_DESKTOP%\cellpose.lnk" (
    echo [OK] Shortcut found on %REAL_DESKTOP%
) else (
    echo [WARNING] Shortcut not found on desktop.
)

echo.
echo [3/3] Done! You can now start Cellpose using the shortcut on your desktop
endlocal
exit /b 0
