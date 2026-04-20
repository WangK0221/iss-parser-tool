param(
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$SpecPath = Join-Path $RepoRoot "ISSParserTool_win10_win11.spec"
$DistPath = Join-Path $RepoRoot "dist\\win10_win11"
$WorkPath = Join-Path $RepoRoot "build\\pyinstaller\\win10_win11"

Write-Host "Building Win10/11 package with Python: $PythonExe"
$ResolvedPythonExe = $PythonExe
$VersionText = & $ResolvedPythonExe --version 2>&1

if ($LASTEXITCODE -ne 0 -or $VersionText -notlike "Python 3.11.*") {
    $ResolvedPythonExe = (& py -3.11 -c "import sys; print(sys.executable)" 2>$null | Select-Object -First 1).Trim()
    if (-not $ResolvedPythonExe) {
        throw "Win10/11 package requires Python 3.11.x, but no Python 3.11 interpreter was found."
    }
    $VersionText = & $ResolvedPythonExe --version 2>&1
}

Write-Host $VersionText

if ($LASTEXITCODE -ne 0) {
    throw "Python executable is invalid: $ResolvedPythonExe"
}

if ($VersionText -notlike "Python 3.11.*") {
    throw "Win10/11 package must be built with Python 3.11.x. Current: $VersionText"
}

& $ResolvedPythonExe -m PyInstaller `
    --noconfirm `
    --clean `
    --distpath $DistPath `
    --workpath $WorkPath `
    $SpecPath

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

Write-Host "Build completed: $DistPath"
