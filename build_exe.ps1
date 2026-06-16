# Build the Flash Drum Designer Windows executable.
#
# Before building, place your icon at assets\icon.ico (optional but recommended).

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

Write-Host "Installing build dependencies..."
py -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
py -m pip install pyinstaller

$iconPath = Join-Path $ProjectRoot "assets\icon.ico"
if (-not (Test-Path $iconPath)) {
    Write-Warning "assets\icon.ico not found. The EXE will build without a custom icon."
    Write-Warning "Add assets\icon.ico and rebuild to apply your icon."
}

Write-Host "Building FlashDrumDesigner.exe..."
py -m PyInstaller (Join-Path $ProjectRoot "FlashDrumDesigner.spec") --noconfirm

$exePath = Join-Path $ProjectRoot "dist\FlashDrumDesigner.exe"
if (Test-Path $exePath) {
    Write-Host ""
    Write-Host "Build complete:"
    Write-Host "  $exePath"
    Write-Host ""
    Write-Host "When you run the EXE, PDF reports are saved next to the executable."
} else {
    throw "Build failed: dist\FlashDrumDesigner.exe was not created."
}