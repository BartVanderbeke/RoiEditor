@echo off
setlocal
set "SCRIPT_DIR=%~dp0.."

if exist "%SCRIPT_DIR%\.venv-win\Scripts\pythonw.exe" (
    start "" /b "%SCRIPT_DIR%\.venv-win\Scripts\pythonw.exe" -m RoiEditor %*
    exit /b 0
)

if exist "%SCRIPT_DIR%\.venv\Scripts\pythonw.exe" (
    start "" /b "%SCRIPT_DIR%\.venv\Scripts\pythonw.exe" -m RoiEditor %*
    exit /b 0
)

where pyw >nul 2>&1
if %errorlevel%==0 (
    start "" /b pyw -m RoiEditor %*
    exit /b 0
)

where pythonw >nul 2>&1
if %errorlevel%==0 (
    start "" /b pythonw -m RoiEditor %*
    exit /b 0
)

echo [ERROR] No suitable pythonw executable found.
exit /b 1
