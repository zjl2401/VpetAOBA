# Package Vpet to release\Vpet, clean old builds, create desktop shortcut
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

Set-Content -Path (Join-Path $OutDir "BUILD_STAMP.txt") -Value ("build=" + $Stamp) -Encoding UTF8

$batLines = @(
    "@echo off",
    "chcp 65001 >nul",
    "cd /d `"%~dp0Vpet`"",
    "start `"`" `"%~dp0Vpet\Vpet.exe`""
)
Set-Content -Path (Join-Path $ReleaseRoot "start_vpet.bat") -Value $batLines -Encoding ASCII

# Keep Chinese shortcut bat as wrapper to ASCII bat (avoid encoding issues)
$cnBat = Join-Path $ReleaseRoot ([string][char]0x542F + [string][char]0x52A8 + "Vpet.bat")
# Prefer simple English name + also write UTF8 BOM Chinese name via .NET
$utf8Bom = New-Object System.Text.UTF8Encoding $true
[System.IO.File]::WriteAllLines(
    (Join-Path $ReleaseRoot "qidong_zhuochong.bat"),
    $batLines,
    $utf8Bom
)
# Chinese filename for user
$cnPath = Join-Path $ReleaseRoot ([char]0x542F + [char]0x52A8 + [char]0x684C + [char]0x5BA0 + ".bat")
[System.IO.File]::WriteAllLines($cnPath, $batLines, $utf8Bom)

$srcBatLines = @(
    "@echo off",
    "chcp 65001 >nul",
    "cd /d `"%~dp0`"",
    "if exist `"release\Vpet\Vpet.exe`" (",
    "  start `"`" `"%~dp0release\Vpet\Vpet.exe`"",
    ") else (",
    "  start `"`" pythonw `"%~dp0vpet_app.py`"",
    ")"
)
[System.IO.File]::WriteAllLines((Join-Path $Root "start_vpet_dev.bat"), $srcBatLines, $utf8Bom)

Write-Host "== desktop shortcut ==" -ForegroundColor Cyan
$exe = Join-Path $OutDir "Vpet.exe"
$wsh = New-Object -ComObject WScript.Shell
$sc = $wsh.CreateShortcut($DesktopLnk)
$sc.TargetPath = $exe
$sc.WorkingDirectory = $OutDir
$sc.IconLocation = ($exe + ",0")
$sc.Description = "Vpet"
$sc.Save()

Write-Host ("OK: " + $exe) -ForegroundColor Green
Write-Host ("Shortcut: " + $DesktopLnk) -ForegroundColor Green
Write-Host ("Stamp: " + $Stamp)
