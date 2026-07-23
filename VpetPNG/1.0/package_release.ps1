# Package Vpet to release\Vpet, clean old builds, create optional desktop shortcut
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\package_release.ps1
#   powershell -ExecutionPolicy Bypass -File .\package_release.ps1 -Shortcut
param(
    [switch]$Shortcut
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$ReleaseRoot = Join-Path $Root "release"
$OutDir = Join-Path $ReleaseRoot "Vpet"
$DistDir = Join-Path $Root "dist\Vpet"
$DesktopLnk = Join-Path ([Environment]::GetFolderPath("Desktop")) "Vpet.lnk"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "== clean old release backups ==" -ForegroundColor Cyan
Get-ChildItem $ReleaseRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -ne "Vpet" -and (
            $_.Name -like "Vpet_old*" -or
            $_.Name -like "Vpet_new*" -or
            $_.Name -like "Vpet_build_*" -or
            $_.Name -like "Vpet_prev_*"
        )
    } |
    ForEach-Object {
        Write-Host ("remove " + $_.Name)
        Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }

Write-Host "== PyInstaller ==" -ForegroundColor Cyan
python -m PyInstaller --noconfirm --clean (Join-Path $Root "Vpet.spec")
if (-not (Test-Path (Join-Path $DistDir "Vpet.exe"))) {
    throw "build failed: missing dist\Vpet\Vpet.exe"
}

Write-Host "== sync release\Vpet ==" -ForegroundColor Cyan
if (Test-Path $OutDir) {
    Remove-Item -LiteralPath $OutDir -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
& robocopy $DistDir $OutDir /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
if (-not (Test-Path (Join-Path $OutDir "Vpet.exe"))) {
    throw "sync failed: missing release\Vpet\Vpet.exe"
}

$BundledSrc = Join-Path $Root "bundled"
$BundledDst = Join-Path $OutDir "bundled"
if (Test-Path $BundledSrc) {
    Write-Host "== copy bundled ==" -ForegroundColor Cyan
    if (Test-Path $BundledDst) {
        Remove-Item -LiteralPath $BundledDst -Recurse -Force
    }
    & robocopy $BundledSrc $BundledDst /E /NFL /NDL /NJH /NJS /nc /ns /np /XD __pycache__ | Out-Null
}

# Minimal data + scrub personal caches if any leaked from previous builds
$DataDst = Join-Path $OutDir "data"
New-Item -ItemType Directory -Force -Path $DataDst | Out-Null
$TypeCacheSrc = Join-Path $Root "data\audio\type_cache.wav"
$AudioDst = Join-Path $DataDst "audio"
New-Item -ItemType Directory -Force -Path $AudioDst | Out-Null
if (Test-Path $TypeCacheSrc) {
    Copy-Item -Force $TypeCacheSrc (Join-Path $AudioDst "type_cache.wav")
}
# Drop personal / regenerable files if present
@(
    "pet_profile.json", "diary.json", "schedules.json", "food_inventory.json",
    "leaderboard.json", "vocab_notebook.json", "pet_id_registry.json",
    "ai_config.json", "app_config.json", "music_config.json",
    "weather_cache.json", "achievements.json"
) | ForEach-Object {
    $p = Join-Path $DataDst $_
    if (Test-Path $p) { Remove-Item -Force $p -ErrorAction SilentlyContinue }
}
$VoiceCache = Join-Path $AudioDst "voice_cache"
if (Test-Path $VoiceCache) { Remove-Item -Recurse -Force $VoiceCache -ErrorAction SilentlyContinue }
Get-ChildItem $AudioDst -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -ne "type_cache.wav" } |
    Remove-Item -Force -ErrorAction SilentlyContinue

Set-Content -Path (Join-Path $OutDir "BUILD_STAMP.txt") -Value ("build=" + $Stamp) -Encoding UTF8

$batLines = @(
    "@echo off",
    "chcp 65001 >nul",
    "cd /d `"%~dp0`"",
    "start `"`" `"%~dp0Vpet.exe`""
)
$utf8Bom = New-Object System.Text.UTF8Encoding $true
[System.IO.File]::WriteAllLines((Join-Path $OutDir "qidong.bat"), $batLines, $utf8Bom)
[System.IO.File]::WriteAllLines((Join-Path $OutDir ([char]0x542F + [char]0x52A8 + ".bat")), $batLines, $utf8Bom)
[System.IO.File]::WriteAllLines((Join-Path $ReleaseRoot "start_vpet.bat"), @(
    "@echo off",
    "chcp 65001 >nul",
    "start `"`" `"%~dp0Vpet\Vpet.exe`""
), $utf8Bom)

Write-Host "== desktop shortcut ==" -ForegroundColor Cyan
if ($Shortcut) {
    $exe = Join-Path $OutDir "Vpet.exe"
    $wsh = New-Object -ComObject WScript.Shell
    $sc = $wsh.CreateShortcut($DesktopLnk)
    $sc.TargetPath = $exe
    $sc.WorkingDirectory = $OutDir
    $sc.IconLocation = ($exe + ",0")
    $sc.Description = "Vpet"
    $sc.Save()
    Write-Host ("Shortcut: " + $DesktopLnk) -ForegroundColor Green
} else {
    Write-Host "skip desktop shortcut (pass -Shortcut to create)" -ForegroundColor Yellow
}

Write-Host ("OK: " + (Join-Path $OutDir "Vpet.exe")) -ForegroundColor Green
Write-Host ("Stamp: " + $Stamp)
