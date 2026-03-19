param(
    [switch]$InstallEmulators = $true,
    [string]$PythonCommand = "python",
    [string]$DosboxPath = "",
    [string]$ScummvmPath = ""
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Find-CommandPath {
    param([string]$Name)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }
    return $null
}

function Resolve-LauncherPath {
    param(
        [string]$Preferred,
        [string[]]$Candidates
    )

    if ($Preferred -and (Test-Path $Preferred)) {
        return (Resolve-Path $Preferred).Path
    }

    foreach ($candidate in $Candidates) {
        if ($candidate -and (Test-Path $candidate)) {
            return (Resolve-Path $candidate).Path
        }
    }

    return ""
}

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

Write-Step "Vérification de Python"
$pythonVersionOutput = & $PythonCommand --version 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Python est introuvable. Installe Python 3.11+ et coche 'Add Python to PATH'."
}
Write-Host $pythonVersionOutput -ForegroundColor Green

Write-Step "Création de l'environnement virtuel"
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    & $PythonCommand -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        throw "Impossible de créer l'environnement virtuel."
    }
}

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$venvPip = Join-Path $projectRoot ".venv\Scripts\pip.exe"

Write-Step "Mise à jour de pip"
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "La mise à jour de pip a échoué."
}

Write-Step "Installation des dépendances Python"
& $venvPip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    throw "L'installation des dépendances Python a échoué."
}

$winget = Find-CommandPath "winget"
if ($InstallEmulators -and $winget) {
    Write-Step "Installation optionnelle de DOSBox et ScummVM via winget"
    & $winget install -e --id DOSBox.DOSBox --accept-source-agreements --accept-package-agreements
    & $winget install -e --id ScummVM.ScummVM --accept-source-agreements --accept-package-agreements
}
elseif ($InstallEmulators) {
    Write-Host "winget introuvable : installation automatique des émulateurs ignorée." -ForegroundColor Yellow
}

Write-Step "Détection des émulateurs"
$resolvedDosbox = Resolve-LauncherPath -Preferred $DosboxPath -Candidates @(
    (Find-CommandPath "dosbox"),
    "$env:ProgramFiles\DOSBox-0.74-3\DOSBox.exe",
    "$env:ProgramFiles\DOSBox Staging\dosbox.exe",
    "$env:ProgramFiles(x86)\DOSBox-0.74-3\DOSBox.exe",
    "$env:ProgramFiles(x86)\DOSBox Staging\dosbox.exe"
)
$resolvedScummvm = Resolve-LauncherPath -Preferred $ScummvmPath -Candidates @(
    (Find-CommandPath "scummvm"),
    "$env:ProgramFiles\ScummVM\scummvm.exe",
    "$env:ProgramFiles(x86)\ScummVM\scummvm.exe"
)

Write-Host ("DOSBox    : {0}" -f ($(if ($resolvedDosbox) { $resolvedDosbox } else { "non détecté" }))) -ForegroundColor Gray
Write-Host ("ScummVM   : {0}" -f ($(if ($resolvedScummvm) { $resolvedScummvm } else { "non détecté" }))) -ForegroundColor Gray

Write-Step "Génération du script de lancement"
$launcher = @"
`$ErrorActionPreference = 'Stop'
Set-Location '$projectRoot'
if (Test-Path '.venv\Scripts\Activate.ps1') {
    . '.venv\Scripts\Activate.ps1'
}
"@

if ($resolvedDosbox) {
    $launcher += "`n`$env:DOSBOX_PATH = '$resolvedDosbox'"
}
if ($resolvedScummvm) {
    $launcher += "`n`$env:SCUMMVM_PATH = '$resolvedScummvm'"
}
$launcher += "`npython app.py`n"

Set-Content -Path (Join-Path $projectRoot "Run-RetroHub.ps1") -Value $launcher -Encoding UTF8

Write-Step "Installation terminée"
Write-Host "1. Double-clique sur Run-RetroHub.ps1 pour lancer l'application." -ForegroundColor Green
Write-Host "2. Si Windows bloque le script, ouvre PowerShell dans ce dossier puis exécute :" -ForegroundColor Green
Write-Host "   Set-ExecutionPolicy -Scope Process Bypass" -ForegroundColor Yellow
Write-Host "   .\Run-RetroHub.ps1" -ForegroundColor Yellow
