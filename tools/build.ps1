param(
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"
$TargetPyInstallerVersion = "5.13.2"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$SpecPath = Join-Path $RepoRoot "app.spec"
$DistPath = Join-Path $RepoRoot "dist"
$WorkPath = Join-Path $RepoRoot "build\\pyinstaller"
$LocalPyInstallerWheel = Join-Path $RepoRoot "tools\\pyinstaller-5.13.2-py3-none-win_amd64.whl"

if (-not $PythonExe) {
    $PyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($PyLauncher) {
        $DetectedPython = & py -3.8 -c "import sys; print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $DetectedPython) {
            $PythonExe = $DetectedPython.Trim()
        }
    }
}

if (-not $PythonExe) {
    $DefaultVenvPython = Join-Path $RepoRoot ".venv-py38\\Scripts\\python.exe"
    if (Test-Path $DefaultVenvPython) {
        $PythonExe = $DefaultVenvPython
    }
}

if (-not $PythonExe -or -not (Test-Path $PythonExe)) {
    throw "Build requires Python 3.8.x. Pass -PythonExe explicitly or install py -3.8."
}

Write-Host "Building package with Python: $PythonExe"
$VersionText = & $PythonExe --version 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Python executable is invalid: $PythonExe"
}

Write-Host $VersionText
if ($VersionText -notlike "Python 3.8.*") {
    throw "Package must be built with Python 3.8.x for Win7 compatibility. Current: $VersionText"
}

$CurrentPyInstallerVersion = & $PythonExe -c "import importlib.metadata as md; print(md.version('pyinstaller'))" 2>$null
if ($LASTEXITCODE -ne 0 -or $CurrentPyInstallerVersion.Trim() -ne $TargetPyInstallerVersion) {
    Write-Host "Installing PyInstaller $TargetPyInstallerVersion for Win7-compatible build..."
    if (Test-Path $LocalPyInstallerWheel) {
        & $PythonExe -m pip install --no-index --no-deps --force-reinstall $LocalPyInstallerWheel
    }
    else {
        & $PythonExe -m pip install "pyinstaller==$TargetPyInstallerVersion"
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install PyInstaller $TargetPyInstallerVersion."
    }
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

$LegacyExePath = Join-Path $DistPath "ISSParserTool.exe"
if (Test-Path $LegacyExePath) {
    Remove-Item -LiteralPath $LegacyExePath -Force
}

Write-Host "Build completed: $DistPath"
