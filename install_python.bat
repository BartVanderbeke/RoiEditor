@echo off
setlocal

echo [1/4] Downloading Python 3.11.0 (64-bit) installer
set "PYTHON_URL=https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe"
set "PYTHON_INSTALLER=%TEMP%\python-3.11.0-amd64.exe"

curl -L -o "%PYTHON_INSTALLER%" "%PYTHON_URL%"
if errorlevel 1 (
    echo [ERROR] Failed to download Python 3.11.0 installer
    exit /b 1
)

echo [2/4] Running silent install for current user
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
if errorlevel 1 (
    echo [ERROR] Python installation failed
    exit /b 1
)

echo [3/4] Verifying installation
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python installation did not succeed
    exit /b 1
)

echo [4/4] Python 3.11.0 installed successfully and is available in PATH
python --version

echo Done.
endlocal
exit /b 0
