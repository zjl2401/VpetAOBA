# Package Vpet to release\Vpet, clean old builds, refresh desktop shortcut + icon
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\package_release.ps1
#   powershell -ExecutionPolicy Bypass -File .\package_release.ps1 -NoShortcut
#   powershell -ExecutionPolicy Bypass -File .\package_release.ps1 -Shortcut   # 兼容旧参数（默认已刷新快捷方式）
param(
    [switch]$Shortcut,
    [switch]$NoShortcut
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$ReleaseRoot = Join-Path $Root "release"
$OutDir = Join-Path $ReleaseRoot "Vpet"
$DistDir = Join-Path $Root "dist\Vpet"
$DesktopLnk = Join-Path ([Environment]::GetFolderPath("Desktop")) "Vpet Aoba.lnk"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

Write-Host "== app icons from stand ==" -ForegroundColor Cyan
python (Join-Path $Root "make_app_icons.py")
if ($LASTEXITCODE -ne 0) {
    if (-not (Test-Path (Join-Path $Root "app_icon.ico"))) {
        throw "make_app_icons failed and no existing app_icon.ico"
    }
    Write-Host "warn: make_app_icons failed; using existing app_icon.ico" -ForegroundColor Yellow
}

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
    "weather_cache.json", "achievements.json", "home_layout.json"
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

Write-Host "== copy docs ==" -ForegroundColor Cyan
$docNames = @("README.md", "INSTALL.txt", "FEATURES.md", "安装说明.txt", "启动说明.txt")
foreach ($doc in $docNames) {
    $src = Join-Path $Root $doc
    if (Test-Path -LiteralPath $src) {
        Copy-Item -LiteralPath $src -Destination (Join-Path $OutDir $doc) -Force
    }
}
# 兜底：按通配拷贝中文安装/启动说明（避免脚本编码导致文件名对不上）
Get-ChildItem -LiteralPath $Root -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "*说明*.txt" -or $_.Name -eq "INSTALL.txt" } |
    ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $OutDir $_.Name) -Force
    }

# 本地存档辅助 bat（打开/清空）
Get-ChildItem -LiteralPath $Root -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "*本地存档*.bat" } |
    ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $OutDir $_.Name) -Force
    }

$batLines = @(
    "@echo off",
    "chcp 65001 >nul",
    "cd /d `"%~dp0`"",
    "start `"`" `"%~dp0Vpet.exe`" --pet --kind aoba"
)
$utf8Bom = New-Object System.Text.UTF8Encoding $true
[System.IO.File]::WriteAllLines((Join-Path $OutDir "qidong.bat"), $batLines, $utf8Bom)
[System.IO.File]::WriteAllLines((Join-Path $OutDir ([char]0x542F + [char]0x52A8 + ".bat")), $batLines, $utf8Bom)
[System.IO.File]::WriteAllLines((Join-Path $OutDir "start_aoba.bat"), @(
    "@echo off",
    "chcp 65001 >nul",
    "cd /d `"%~dp0`"",
    "start `"`" `"%~dp0Vpet.exe`" --pet --kind aoba"
), $utf8Bom)
# 本包无伊得立绘：勿再提供假 start_eiden.bat。若存在旧文件则删掉。
$fakeEidenBat = Join-Path -Path $OutDir -ChildPath "start_eiden.bat"
if ($fakeEidenBat -and (Test-Path -LiteralPath $fakeEidenBat)) {
    Remove-Item -LiteralPath $fakeEidenBat -Force -ErrorAction SilentlyContinue
    Write-Host "Removed fake start_eiden.bat (use VpetEidenPet instead)" -ForegroundColor Yellow
}
[System.IO.File]::WriteAllLines((Join-Path $ReleaseRoot "start_vpet.bat"), @(
    "@echo off",
    "chcp 65001 >nul",
    "start `"`" `"%~dp0Vpet\Vpet.exe`" --pet --kind aoba"
), $utf8Bom)

# Always copy app_icon into release (missing ico => blank shortcut icon)
$icoSrc = Join-Path $Root "app_icon.ico"
$icoDst = Join-Path $OutDir "app_icon.ico"
if (Test-Path -LiteralPath $icoSrc) {
    Copy-Item -Force -LiteralPath $icoSrc -Destination $icoDst
    Write-Host ("copied app_icon.ico -> " + $icoDst) -ForegroundColor Green
} else {
    Write-Host "warn: missing root app_icon.ico" -ForegroundColor Yellow
}

# Sync Desktop\Vpet sidecar if present
$DesktopFolder = [Environment]::GetFolderPath("Desktop")
if ([string]::IsNullOrWhiteSpace($DesktopFolder)) {
    $DesktopFolder = Join-Path $env:USERPROFILE "Desktop"
}
$DesktopVpet = Join-Path $DesktopFolder "Vpet"

# 桌面 _internal 里若残留旧 pet.py，会盖住新包；每次同步后强制写入当前源码模块
function Sync-DesktopInternalModules([string]$Root) {
    $internal = Join-Path $Root "_internal"
    if (-not (Test-Path -LiteralPath $internal)) {
        New-Item -ItemType Directory -Path $internal -Force | Out-Null
    }
    $srcRoot = $PSScriptRoot
    $mods = @(
        "pet.py", "pet_outfit.py", "home_cottage.py", "panel_decor.py",
        "peer_friendship.py", "rhythm_chart_editor.py", "vpet_app.py",
        "vpet_launcher.py", "voice_audio.py", "voice_system.py",
        "bundled_paths.py", "media_bundled.py", "pet_id_cloud.py",
        "app_scene_desktop.py"
    )
    foreach ($name in $mods) {
        $src = Join-Path $srcRoot $name
        if (Test-Path -LiteralPath $src) {
            Copy-Item -Force -LiteralPath $src -Destination (Join-Path $internal $name)
        }
    }
    Write-Host ("synced source modules -> " + $internal) -ForegroundColor Green
}

if (Test-Path -LiteralPath $DesktopVpet) {
    Write-Host ("== sync Desktop\Vpet <= " + $OutDir) -ForegroundColor Cyan
    & robocopy $OutDir $DesktopVpet /E /NFL /NDL /NJH /NJS /nc /ns /np /R:1 /W:1 | Out-Null
    Sync-DesktopInternalModules $DesktopVpet
    if (Test-Path -LiteralPath $icoDst) {
        Copy-Item -Force -LiteralPath $icoDst -Destination (Join-Path $DesktopVpet "app_icon.ico")
    }
}

Write-Host "== desktop shortcut ==" -ForegroundColor Cyan
# Refresh Aoba shortcut by default; skip only with -NoShortcut
if (-not $NoShortcut) {
    # Prefer Desktop\Vpet so exe + ico stay together
    $exe = Join-Path $OutDir "Vpet.exe"
    $workDir = $OutDir
    $deskExe = Join-Path $DesktopVpet "Vpet.exe"
    if (Test-Path -LiteralPath $deskExe) {
        $exe = $deskExe
        $workDir = $DesktopVpet
    }
    $icoForLnk = Join-Path $workDir "app_icon.ico"
    if (-not (Test-Path -LiteralPath $icoForLnk)) {
        $icoForLnk = $icoDst
    }
    if (Test-Path -LiteralPath $icoForLnk) {
        $iconLoc = "$icoForLnk,0"
    } else {
        $iconLoc = "$exe,0"
    }
    $wsh = New-Object -ComObject WScript.Shell
    $desktop = $DesktopFolder
    if ([string]::IsNullOrWhiteSpace($desktop)) {
        throw "Desktop folder not found"
    }
    # Only write Vpet Aoba.lnk (never create Vpet Eiden.lnk)
    $lnk = Join-Path $desktop "Vpet Aoba.lnk"
    if ([string]::IsNullOrWhiteSpace($lnk) -or -not $lnk.ToLower().EndsWith(".lnk")) {
        throw ("shortcut path invalid: " + $lnk)
    }
    $sc = $wsh.CreateShortcut($lnk)
    $sc.TargetPath = $exe
    $sc.Arguments = "--pet --kind aoba"
    $sc.WorkingDirectory = $workDir
    $sc.IconLocation = $iconLoc
    $sc.Description = "Aoba - Ctrl+Shift+V"
    $sc.Save()
    Write-Host ("Shortcut: " + $lnk + " => [--pet --kind aoba]") -ForegroundColor Green
    # Remove Vpet Eiden.lnk only if it wrongly points at this Aoba package
    $badEiden = Join-Path $desktop "Vpet Eiden.lnk"
    if (Test-Path -LiteralPath $badEiden) {
        try {
            $chk = $wsh.CreateShortcut($badEiden)
            $tp = [string]$chk.TargetPath
            $outEsc = $OutDir.Replace('\', '\\')
            $pointsHere = ($tp -like ("*" + $outEsc + "*")) -or ($tp -match '\\Desktop\\Vpet\\Vpet\.exe$')
            if ($pointsHere) {
                Remove-Item -Force -LiteralPath $badEiden -ErrorAction SilentlyContinue
                Write-Host "Removed bad Vpet Eiden.lnk pointing at Aoba package" -ForegroundColor Yellow
            }
        } catch {
        }
    }
    foreach ($legacyName in @("Vpet.lnk", "VpetAoba.lnk")) {
        $legacyLnk = Join-Path $desktop $legacyName
        if (Test-Path -LiteralPath $legacyLnk) {
            Remove-Item -Force -LiteralPath $legacyLnk -ErrorAction SilentlyContinue
            Write-Host ("Removed legacy: " + $legacyLnk) -ForegroundColor Yellow
        }
    }
    Write-Host ("Icon: " + $iconLoc) -ForegroundColor Green
} else {
    Write-Host "skip desktop shortcut (-NoShortcut)" -ForegroundColor Yellow
}

Write-Host ("OK: " + (Join-Path $OutDir "Vpet.exe")) -ForegroundColor Green
Write-Host ("Stamp: " + $Stamp)
