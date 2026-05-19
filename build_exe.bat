@echo off
setlocal

echo Installing/updating build dependencies...
py -m pip install -r requirements.txt
if errorlevel 1 exit /b %errorlevel%

echo Building Pixel Zombie Siege...
py -m PyInstaller --noconfirm --clean --onedir --windowed --name PixelZombieSiege --add-data "assets;assets" main.py
if errorlevel 1 exit /b %errorlevel%

echo.
echo Build complete:
echo   dist\PixelZombieSiege\PixelZombieSiege.exe
echo.
echo Save data for the EXE is stored in:
echo   %%APPDATA%%\PixelZombieSiege\save_data.json

endlocal
