$ErrorActionPreference = "Stop"

Write-Host "Installing/updating build dependencies..."
py -m pip install -r requirements.txt

Write-Host "Building Pixel Zombie Siege..."
py -m PyInstaller `
  --noconfirm `
  --clean `
  --onedir `
  --windowed `
  --name PixelZombieSiege `
  --add-data "assets;assets" `
  main.py

Write-Host ""
Write-Host "Build complete:"
Write-Host "  dist\PixelZombieSiege\PixelZombieSiege.exe"
Write-Host ""
Write-Host "Save data for the EXE is stored in:"
Write-Host "  %APPDATA%\PixelZombieSiege\save_data.json"
