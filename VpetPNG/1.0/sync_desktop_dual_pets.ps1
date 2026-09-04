# 把本仓库的跨宠友情代码同步到桌面两个目录：
#   %USERPROFILE%\Desktop\VpetAOBA      → 苍叶（KIND=aoba）
#   %USERPROFILE%\Desktop\VpetEidenPet  → 伊得（KIND=eiden）
# 并刷新桌面快捷方式。
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not (Test-Path (Join-Path $repoRoot "VpetPNG\1.0\pet.py"))) {
  # 若脚本放在仓库根目录
  if (Test-Path (Join-Path $PSScriptRoot "VpetPNG\1.0\pet.py")) {
    $repoRoot = $PSScriptRoot
  } elseif (Test-Path (Join-Path $PSScriptRoot "pet.py")) {
    $repoRoot = Split-Path -Parent $PSScriptRoot
  }
}
$src = Join-Path $repoRoot "VpetPNG\1.0"
if (-not (Test-Path (Join-Path $src "pet.py"))) {
  Write-Host "找不到源码: $src\pet.py" -ForegroundColor Red
  exit 1
}

$desktop = [Environment]::GetFolderPath("Desktop")
$targets = @(
  @{ Path = (Join-Path $desktop "VpetAOBA"); Kind = "aoba"; Label = "苍叶" },
  @{ Path = (Join-Path $desktop "VpetEidenPet"); Kind = "eiden"; Label = "伊得" }
)

$copyFiles = @(
  "pet.py",
  "peer_friendship.py",
  "voice_system.py",
  "voice_audio.py",
  "panel_decor.py",
  "bundled_paths.py",
  "media_bundled.py",
  "desktop_clock.py",
  "vpet_app.py",
  "start_aoba.bat",
  "start_eiden.bat",
  "start_vpet_dev.bat",
  "update_desktop_shortcuts.ps1",
  "更新桌面快捷方式.bat"
)

function Resolve-PetCodeDir([string]$root) {
  $cands = @(
    (Join-Path $root "VpetPNG\1.0"),
    (Join-Path $root "1.0"),
    $root
  )
  foreach ($c in $cands) {
    if (Test-Path (Join-Path $c "pet.py")) { return $c }
  }
  $preferred = Join-Path $root "VpetPNG\1.0"
  New-Item -ItemType Directory -Force -Path $preferred | Out-Null
  return $preferred
}

function Sync-OnePet($target) {
  $root = $target.Path
  $kind = $target.Kind
  $label = $target.Label
  if (-not (Test-Path $root)) {
    Write-Host "创建目录: $root" -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $root | Out-Null
  }

  # 若是 git 仓库，尽量拉到功能分支
  $gitDir = Join-Path $root ".git"
  if (Test-Path $gitDir) {
    Push-Location $root
    try {
      git fetch origin 2>$null
      git checkout cursor/auto-restore-companion-c4c2 2>$null
      git pull origin cursor/auto-restore-companion-c4c2 2>$null
      Write-Host "[$label] git 已尝试更新到 cursor/auto-restore-companion-c4c2" -ForegroundColor Cyan
    } catch {
      Write-Host "[$label] git 更新跳过: $_" -ForegroundColor DarkYellow
    } finally {
      Pop-Location
    }
  }

  $dest = Resolve-PetCodeDir $root
  foreach ($f in $copyFiles) {
    $from = Join-Path $src $f
    if (-not (Test-Path $from)) { continue }
    Copy-Item -Force -Path $from -Destination (Join-Path $dest $f)
  }
  # 角色标记：双开时凭文件夹/KIND 自动识别，面板显示对应「友情」
  Set-Content -Path (Join-Path $dest "KIND.txt") -Value $kind -Encoding UTF8
  # 根目录也放一份，方便从仓库根启动
  Set-Content -Path (Join-Path $root "KIND.txt") -Value $kind -Encoding UTF8
  # 版本戳：方便确认桌面目录是否已同步到最新源码（勿再跑旧 exe）
  $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $stampBody = @"
branch=cursor/auto-restore-companion-c4c2
kind=$kind
synced_at=$stamp
prefer=pet.py
"@
  Set-Content -Path (Join-Path $dest "SYNC_STAMP.txt") -Value $stampBody -Encoding UTF8
  Set-Content -Path (Join-Path $root "SYNC_STAMP.txt") -Value $stampBody -Encoding UTF8

  # 该目录默认启动脚本（优先 pet.py，避免旧 release exe 挡住更新）
  $boot = Join-Path $dest "启动本宠.bat"
  $bootBody = @"
@echo off
chcp 65001 >nul
cd /d "%~dp0"
set VPET_KIND=$kind
if exist "pet.py" (
  start "" pythonw "%~dp0pet.py" --kind $kind
) else if exist "release\Vpet\Vpet.exe" (
  start "" "%~dp0release\Vpet\Vpet.exe" --kind $kind
) else (
  start "" pythonw "%~dp0vpet_app.py" --kind $kind
)
"@
  Set-Content -Path $boot -Value $bootBody -Encoding ASCII

  $rootBoot = Join-Path $root "启动本宠.bat"
  $rel = $dest.Substring($root.Length).TrimStart('\')
  if ([string]::IsNullOrWhiteSpace($rel)) {
    Copy-Item -Force $boot $rootBoot
  } else {
    $rootBody = @"
@echo off
chcp 65001 >nul
cd /d "%~dp0"
call "%~dp0$rel\启动本宠.bat"
"@
    Set-Content -Path $rootBoot -Value $rootBody -Encoding ASCII
  }

  Write-Host "[$label] 已同步 → $dest (KIND=$kind)" -ForegroundColor Green
  return @{ Label = $label; Boot = $rootBoot; Kind = $kind }
}

$results = @()
foreach ($t in $targets) {
  $results += Sync-OnePet $t
}

# 桌面快捷方式分别指向两个目录
$shell = New-Object -ComObject WScript.Shell
$icon = Join-Path $src "app_icon.ico"
foreach ($r in $results) {
  $name = if ($r.Kind -eq "aoba") { "苍叶桌宠" } else { "伊得桌宠" }
  $lnkPath = Join-Path $desktop "$name.lnk"
  $sc = $shell.CreateShortcut($lnkPath)
  $sc.TargetPath = $r.Boot
  $sc.WorkingDirectory = (Split-Path -Parent $r.Boot)
  $sc.WindowStyle = 7
  $sc.Description = "$name（跨宠友情）"
  if (Test-Path $icon) { $sc.IconLocation = $icon }
  $sc.Save()
  Write-Host "桌面快捷方式: $lnkPath" -ForegroundColor Green
}

Write-Host ""
Write-Host "完成。请先关掉正在运行的桌宠，再分别点「苍叶桌宠」「伊得桌宠」。" -ForegroundColor Green
Write-Host "面板应出现「友情」；两只靠近半个身位内会打招呼并涨好感。" -ForegroundColor Green
