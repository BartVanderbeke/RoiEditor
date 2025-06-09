@echo off
echo [1/4] Searching for python.exe
set "PY_PATH="
for /f "delims=" %%P in ('where python 2^>nul') do (
    set "PY_PATH=%%P"
    goto :found_python
)

:found_python
if not defined PY_PATH (
    echo [1/4] [WARNING] python was not found. Please install python and try again.
    exit /b 1
) else (
    echo [1/4] [OK] python is already available, no need to install.
)

echo [2/4] Searching for pythonw.exe
set "PYW_PATH="
for /f "delims=" %%P in ('where pythonw 2^>nul') do (
    set "PYW_PATH=%%P"
    goto :found_pythonw
)

:found_pythonw
if not defined PYW_PATH (
    echo [2/4] [WARNING] pythonw was not found. Please install pythonw and try again.
    exit /b 1
) else (
    echo [2/4] [OK] pythonw is already available, no need to install.
)

echo [3/4] Searching for cellpose
pip show cellpose >nul 2>&1
if %errorlevel%==0 (
    echo [3/4] [OK] cellpose has already been installed.
) else (
    echo [3/4] [WARNING] cellpose has not yet been installed.
)

for /f "delims=" %%D in ('powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"') do (
    set "REAL_DESKTOP=%%D"
)
if exist "%REAL_DESKTOP%\cellpose.lnk" (
    echo [3/4] [OK] Shortcut for cellpose found on %REAL_DESKTOP% .
) else (
    echo [3/4] [WARNING] Shortcut not found for cellpose.
)

echo [4/4] Searching for RoiEditor
pip show RoiEditor >nul 2>&1
if %errorlevel%==0 (
    echo [4/4] [OK] RoiEditor has already been installed.
) else (
    echo [4/4] [WARNING] RoiEditor has not yet been installed.
)

for /f "delims=" %%D in ('powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"') do (
    set "REAL_DESKTOP=%%D"
)
if exist "%REAL_DESKTOP%\RoiEditor.lnk" (
    echo [4/4] [OK] Shortcut for RoiEditor found on %REAL_DESKTOP% .
) else (
    echo [4/4] [WARNING] Shortcut not found for RoiEditor.
)
