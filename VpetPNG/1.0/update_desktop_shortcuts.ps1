# 在当前用户桌面创建「苍叶桌宠」「伊得桌宠」快捷方式
# 优先指向 Desktop\VpetAOBA / VpetEidenPet；否则指向本目录启动脚本
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$desktop = [Environment]::GetFolderPath("Desktop")
$icon = Join-Path $here "app_icon.ico"
$shell = New-Object -ComObject WScript.Shell

function Resolve-Boot([string]$folderName, [string]$fallbackBat, [string]$kind) {
  $root = Join-Path $desktop $folderName
  $cands = @(
    (Join-Path $root "启动本宠.bat"),
    (Join-Path $root "VpetPNG\1.0\启动本宠.bat"),
    (Join-Path $root "VpetPNG\1.0\start_$kind.bat"),
    (Join-Path $here $fallbackBat)
  )
  foreach ($c in $cands) {
    if (Test-Path $c) { return $c }
  }
  return (Join-Path $here $fallbackBat)
}

function New-PetShortcut {
  param(
    [string]$Name,
    [string]$Target,
    [string]$Description
  )
  if (-not (Test-Path $Target)) {
    Write-Host "缺少启动脚本: $Target" -ForegroundColor Red
    return $false
  }
  $lnkPath = Join-Path $desktop "$Name.lnk"
  $sc = $shell.CreateShortcut($lnkPath)
  $sc.TargetPath = $Target
  $sc.WorkingDirectory = (Split-Path -Parent $Target)
  $sc.WindowStyle = 7
  $sc.Description = $Description
  if (Test-Path $icon) { $sc.IconLocation = $icon }
  $sc.Save()
  Write-Host "已更新: $lnkPath -> $Target" -ForegroundColor Green
  return $true
}

$aobaBoot = Resolve-Boot "VpetAOBA" "start_aoba.bat" "aoba"
$eidenBoot = Resolve-Boot "VpetEidenPet" "start_eiden.bat" "eiden"

$ok1 = New-PetShortcut -Name "苍叶桌宠" -Target $aobaBoot -Description "苍叶（可与伊得双开涨友情）"
$ok2 = New-PetShortcut -Name "伊得桌宠" -Target $eidenBoot -Description "伊得（可与苍叶双开涨友情）"

foreach ($legacy in @("Vpet", "启动 Vpet", "VpetAOBA", "桌宠")) {
  $legacyLnk = Join-Path $desktop "$legacy.lnk"
  if (Test-Path $legacyLnk) {
    $sc = $shell.CreateShortcut($legacyLnk)
    $sc.TargetPath = $eidenBoot
    $sc.WorkingDirectory = (Split-Path -Parent $eidenBoot)
    $sc.WindowStyle = 7
    $sc.Description = "伊得桌宠（已指向新启动脚本）"
    if (Test-Path $icon) { $sc.IconLocation = $icon }
    $sc.Save()
    Write-Host "已改写旧快捷方式: $legacyLnk" -ForegroundColor Cyan
  }
}

if ($ok1 -and $ok2) {
  Write-Host ""
  Write-Host "完成。请分别打开「苍叶桌宠」和「伊得桌宠」，面板应有「友情」。" -ForegroundColor Green
  exit 0
}
exit 1
