<#
.SYNOPSIS
    Instala o PiP Cam (Portable) no sistema.
.DESCRIPTION
    Baixa a última versão do PipCamPortable.exe do GitHub Releases e cria
    atalhos no Desktop e no Menu Iniciar.
    Uso: irm https://raw.githubusercontent.com/silv4b/pip-cam/main/install.ps1 | iex
#>

$ErrorActionPreference = "Stop"

$RepoOwner = "silv4b"
$RepoName = "pip-cam"
$ExeName = "PipCamPortable.exe"
$InstallDir = Join-Path $env:LOCALAPPDATA "PiP_Cam" "portable"
$DesktopLnk = Join-Path $([Environment]::GetFolderPath("Desktop")) "PiP Cam.lnk"
$StartMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\PiP Cam"
$StartMenuLnk = Join-Path $StartMenuDir "PiP Cam.lnk"

Write-Host "==> PiP Cam Installer" -ForegroundColor Cyan
Write-Host ""
Write-Host "Repositorio: $RepoOwner/$RepoName"
Write-Host "Destino:     $InstallDir"
Write-Host ""

# 1. Criar diretório de instalação
if (Test-Path $InstallDir) {
    Write-Host "[AVISO] Diretorio ja existe. Os arquivos serao substituidos." -ForegroundColor Yellow
    Remove-Item "$InstallDir\*" -Recurse -Force -ErrorAction SilentlyContinue
} else {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

# 2. Descobrir a última release via API
Write-Host "[1/4] Obtendo informacoes da ultima release..." -ForegroundColor Green
try {
    $ApiUrl = "https://api.github.com/repos/$RepoOwner/$RepoName/releases/latest"
    $Release = Invoke-RestMethod -Uri $ApiUrl -Headers @{ "Accept" = "application/vnd.github.v3+json" }
    $Version = $Release.tag_name
    Write-Host "      Versao encontrada: $Version"
} catch {
    Write-Host "[ERRO] Nao foi possivel obter a ultima release: $_" -ForegroundColor Red
    exit 1
}

# 3. Localizar o asset PipCamPortable.exe na release
$Asset = $Release.assets | Where-Object { $_.name -eq $ExeName }
if (-not $Asset) {
    Write-Host "[ERRO] Asset '$ExeName' nao encontrado na release $Version." -ForegroundColor Red
    Write-Host "      Assets disponiveis: $($Release.assets.name -join ', ')" -ForegroundColor Yellow
    exit 1
}

# 4. Baixar o executável
Write-Host "[2/4] Baixando PipCamPortable.exe..." -ForegroundColor Green
$ExePath = Join-Path $InstallDir $ExeName
try {
    $WebClient = New-Object System.Net.WebClient
    $WebClient.Headers.Add("User-Agent", "PiPCam-Installer")
    $WebClient.DownloadFile($Asset.browser_download_url, $ExePath)
    Write-Host "      Salvo em: $ExePath"
} catch {
    Write-Host "[ERRO] Falha ao baixar o arquivo: $_" -ForegroundColor Red
    exit 1
}

# 5. Verificar integridade
if (-not (Test-Path $ExePath)) {
    Write-Host "[ERRO] Arquivo nao encontrado apos download." -ForegroundColor Red
    exit 1
}
$FileSize = (Get-Item $ExePath).Length
Write-Host "      Tamanho: $("{0:N0}" -f $FileSize) bytes"

# 6. Criar atalho no Desktop
Write-Host "[3/4] Criando atalho no Desktop..." -ForegroundColor Green
try {
    $WScriptShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WScriptShell.CreateShortcut($DesktopLnk)
    $Shortcut.TargetPath = $ExePath
    $Shortcut.WorkingDirectory = $InstallDir
    $Shortcut.Description = "PiP Cam $Version"
    $Shortcut.IconLocation = "$ExePath, 0"
    $Shortcut.Save()
    Write-Host "      $DesktopLnk"
} catch {
    Write-Host "[AVISO] Nao foi possivel criar atalho no Desktop: $_" -ForegroundColor Yellow
}

# 7. Criar atalho no Menu Iniciar
Write-Host "[4/4] Criando atalho no Menu Iniciar..." -ForegroundColor Green
try {
    New-Item -ItemType Directory -Path $StartMenuDir -Force | Out-Null
    $WScriptShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WScriptShell.CreateShortcut($StartMenuLnk)
    $Shortcut.TargetPath = $ExePath
    $Shortcut.WorkingDirectory = $InstallDir
    $Shortcut.Description = "PiP Cam $Version"
    $Shortcut.IconLocation = "$ExePath, 0"
    $Shortcut.Save()
    Write-Host "      $StartMenuLnk"
} catch {
    Write-Host "[AVISO] Nao foi possivel criar atalho no Menu Iniciar: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Instalacao concluida! ===" -ForegroundColor Cyan
Write-Host "PiP Cam $Version foi instalado em:" -ForegroundColor White
Write-Host "  $InstallDir" -ForegroundColor White
Write-Host ""
Write-Host "Para executar, use o atalho no Desktop ou Menu Iniciar." -ForegroundColor White
Write-Host "Comando manual:" -ForegroundColor Gray
Write-Host "  & '$ExePath'" -ForegroundColor Gray
