@echo off
setlocal

echo [1/3] Searching for python.exe
for /f "delims=" %%P in ('where python 2^>nul') do set "PY_PATH=%%P"
if not defined PY_PATH (
    echo [ERROR] Python was not found. Please install Python and try again.
    exit /b 1
)
echo [OK] Python found: %PY_PATH%

echo.
echo [2/3] Installing cellpose
"%PY_PATH%" -m pip install --upgrade pip >nul 2>&1
"%PY_PATH%" -m pip install cellpose
if errorlevel 1 (
    echo [ERROR] Failed to install Cellpose.
    exit /b 1
)
echo [OK] cellpose successfully installed

echo.
echo [3/3] Creating desktop shortcut for cellpose
powershell -NoProfile -Command ^
 "$s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'cellpose.lnk')); " ^
 "$s.TargetPath = '%PY_PATH%'; " ^
 "$s.Arguments = '-m cellpose'; " ^
 "$s.WorkingDirectory = '%~dp0'; " ^
 "$s.IconLocation = '%~dp0cellpose.ico'; " ^
 "$s.Save()"

if exist "%USERPROFILE%\Desktop\cellpose.lnk" (
    echo [OK] Shortcut for cellpose created on desktop
) else (
    echo [WARNING] Shortcut could not be created.
	exit /b 1
)

echo.
echo Done! You can now start Cellpose via the shortcut on your desktop
endlocal
exit /b 0
