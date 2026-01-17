# Clear Python bytecode cache
# This script removes all __pycache__ directories and .pyc files

Write-Host "Clearing Python bytecode cache..."

# Remove __pycache__ directories
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Write-Host "[OK] Removed __pycache__ directories"

# Remove .pyc files
Get-ChildItem -Path . -Recurse -File -Filter "*.pyc" | Remove-Item -Force
Write-Host "[OK] Removed .pyc files"

# Remove .pyo files
Get-ChildItem -Path . -Recurse -File -Filter "*.pyo" | Remove-Item -Force
Write-Host "[OK] Removed .pyo files"

Write-Host "Cache clearing complete!"
