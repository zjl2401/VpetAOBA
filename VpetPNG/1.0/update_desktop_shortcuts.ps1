# 在当前用户桌面创建「苍叶桌宠」「伊得桌宠」快捷方式
# 用法：在 VpetPNG\1.0 目录运行，或双击「更新桌面快捷方式.bat」
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$desktop = [Environment]::GetFolderPath("Desktop")
$icon = Join-Path $here "app_icon.ico"
if (-not (Test-Path $icon)) {
  $icon = "%SystemRoot%\System32\shell32.dll,0"
}

$shell = New-Object -ComObject WScript.Shell

function New-PetShortcut {
  param(
    [string]$Name,
    [string]$BatName,
    [string]$Description
  )
  $bat = Join-Path $here $BatName
  if (-not (Test-Path $bat)) {
    Write-Host "缺少启动脚本: $bat" -ForegroundColor Red
    return $false
  }
  $lnkPath = Join-Path $desktop "$Name.lnk"
  $sc = $shell.CreateShortcut($lnkPath)
  $sc.TargetPath = $bat
  $sc.WorkingDirectory = $here
  $sc.WindowStyle = 7
  $sc.Description = $Description
  if (Test-Path (Join-Path $here "app_icon.ico")) {
    $sc.IconLocation = (Join-Path $here "app_icon.ico")
  }
  $sc.Save()
  Write-Host "已更新: $lnkPath" -ForegroundColor Green
  return $true
}

$ok1 = New-PetShortcut -Name "苍叶桌宠" -BatName "start_aoba.bat" -Description "以苍叶身份启动（可与伊得双开涨友情）"
$ok2 = New-PetShortcut -Name "伊得桌宠" -BatName "start_eiden.bat" -Description "以伊得身份启动（可与苍叶双开涨友情）"

# 兼容旧名：若桌面还有「Vpet」「启动 Vpet」等，一并指到伊得（默认角色）
foreach ($legacy in @("Vpet", "启动 Vpet", "VpetAOBA", "桌宠")) {
  $legacyLnk = Join-Path $desktop "$legacy.lnk"
  if (Test-Path $legacyLnk) {
    $bat = Join-Path $here "start_eiden.bat"
    if (Test-Path $bat) {
      $sc = $shell.CreateShortcut($legacyLnk)
      $sc.TargetPath = $bat
      $sc.WorkingDirectory = $here
      $sc.WindowStyle = 7
      $sc.Description = "伊得桌宠（已指向新启动脚本）"
      if (Test-Path (Join-Path $here "app_icon.ico")) {
        $sc.IconLocation = (Join-Path $here "app_icon.ico")
      }
      $sc.Save()
      Write-Host "已改写旧快捷方式: $legacyLnk -> start_eiden.bat" -ForegroundColor Cyan
    }
  }
}

if ($ok1 -and $ok2) {
  Write-Host ""
  Write-Host "完成。桌面应有「苍叶桌宠」和「伊得桌宠」；双开后靠近即可涨友情。" -ForegroundColor Green
  exit 0
}
exit 1
