param(
    [string]$PythonExe = ".venv-win7\\Scripts\\python.exe"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$SpecPath = Join-Path $RepoRoot "ISSParserTool_win7.spec"
$DistPath = Join-Path $RepoRoot "dist\\win7"
$WorkPath = Join-Path $RepoRoot "build\\pyinstaller\\win7"

if (-not (Test-Path $PythonExe)) {
    throw "Win7 build requires a dedicated Python 3.8 environment. Missing: $PythonExe"
}

Write-Host "Building Win7 package with Python: $PythonExe"
$VersionText = & $PythonExe --version 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Python executable is invalid: $PythonExe"
}

Write-Host $VersionText
if ($VersionText -notlike "Python 3.8.*") {
    throw "Win7 package must be built with Python 3.8.x. Current: $VersionText"
}

& $PythonExe -m PyInstaller `
    --noconfirm `
    --clean `
    --distpath $DistPath `
    --workpath $WorkPath `
    $SpecPath

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

Write-Host "Build completed: $DistPath"
