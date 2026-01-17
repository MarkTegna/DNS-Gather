# Create distribution package for DNS-Gather

Write-Host "Creating distribution package..." -ForegroundColor Cyan

# Get version from version.py
$versionFile = "dns_gather\version.py"
$versionContent = Get-Content $versionFile -Raw
if ($versionContent -match '__version__\s*=\s*[''"]([^''"]+)[''"]') {
    $version = $matches[1]
    Write-Host "[OK] Version: $version" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Could not read version from $versionFile" -ForegroundColor Red
    exit 1
}

# Create dist directory if it doesn't exist
if (-not (Test-Path "dist")) {
    New-Item -ItemType Directory -Path "dist" | Out-Null
}

# Create Archive directory if it doesn't exist
if (-not (Test-Path "Archive")) {
    New-Item -ItemType Directory -Path "Archive" | Out-Null
}

# Create ZIP filename
$zipName = "DNS-Gather_v$version.zip"
$zipPath = "dist\$zipName"
$archivePath = "Archive\$zipName"

# Remove old ZIP if it exists
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
    Write-Host "[OK] Removed old ZIP file" -ForegroundColor Yellow
}

# Create ZIP file
Write-Host "[+] Creating ZIP file: $zipName" -ForegroundColor Cyan

# Check if files exist
if (-not (Test-Path "dist\DNS-Gather.exe")) {
    Write-Host "[ERROR] DNS-Gather.exe not found in dist directory" -ForegroundColor Red
    Write-Host "[INFO] Run build_executable.py first" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path "dist\DNS-Gather.ini")) {
    Write-Host "[ERROR] DNS-Gather.ini not found in dist directory" -ForegroundColor Red
    exit 1
}

# Create ZIP
Compress-Archive -Path "dist\DNS-Gather.exe", "dist\DNS-Gather.ini" -DestinationPath $zipPath -Force

if (Test-Path $zipPath) {
    Write-Host "[OK] Created: $zipPath" -ForegroundColor Green
    
    # Copy to Archive
    Copy-Item $zipPath $archivePath -Force
    Write-Host "[OK] Copied to: $archivePath" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Failed to create ZIP file" -ForegroundColor Red
    exit 1
}

Write-Host "`n[OK] Distribution package created successfully!" -ForegroundColor Green
