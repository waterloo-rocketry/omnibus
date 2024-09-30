# Ensure this script is run as a PowerShell script
if (-not $IsWindows) {
    Write-Host "This script is intended for Windows environments only."
    exit
}

Write-Host "`n----- Upgrading pip -----"
pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { exit }

Write-Host "`n----- Installing tools -----"
pip install wheel
if ($LASTEXITCODE -ne 0) { exit }

# Install requirements
Write-Host "`n----- Installing global requirements -----"
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { exit }

Write-Host "`n----- Installing NI source requirements -----"
pip install -r sources/ni/requirements.txt
if ($LASTEXITCODE -ne 0) { exit }

Write-Host "`n----- Installing Parsley source requirements -----"
pip install -r sources/parsley/requirements.txt
if ($LASTEXITCODE -ne 0) { exit }

Write-Host "`n----- Installing Dashboard sink requirements -----"
pip install -r sinks/dashboard/requirements.txt
if ($LASTEXITCODE -ne 0) { exit }

# Install local libraries
Write-Host "`n----- Installing Omnibus library -----"
pip install -e .
if ($LASTEXITCODE -ne 0) { exit }

Write-Host "`n----- Installing Parsley library -----"
git submodule update --init --recursive
if ($LASTEXITCODE -ne 0) { exit }
pip install -e ./parsley
if ($LASTEXITCODE -ne 0) { exit }

Write-Host "`n----- Omnibus setup successfully -----"
