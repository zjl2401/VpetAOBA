# Build debug APK (needs Android SDK + JDK 17)
# Usage: .\build_debug.ps1 in VpetMobile folder

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

$candidates = @(
    (Join-Path $root ".android-sdk"),
    (Join-Path $env:LOCALAPPDATA "Android\Sdk")
)
$sdk = $candidates | Where-Object { Test-Path (Join-Path $_ "platforms\android-34") } | Select-Object -First 1
if (-not $sdk) {
    Write-Host "Android SDK platforms;android-34 not found."
    Write-Host "  sdkmanager platforms;android-34 build-tools;34.0.0 platform-tools"
    exit 1
}

$props = Join-Path $root "local.properties"
$sdkProp = $sdk -replace '\\', '/'
"sdk.dir=$sdkProp" | Set-Content -Path $props -Encoding ASCII

Write-Host "Building debug APK with SDK: $sdk"

if (-not $env:JAVA_HOME -or -not (Test-Path (Join-Path $env:JAVA_HOME "bin\java.exe"))) {
    $jdkList = @()
    $jdkList += "C:\Program Files\Microsoft\jdk-17.0.19.10-hotspot"
    $jdkList += @(Get-ChildItem "C:\Program Files\Microsoft\jdk-17*" -Directory -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
    $jdkList += (Join-Path $env:ProgramFiles "Android\Android Studio\jbr")
    $jdkList += (Join-Path $env:LOCALAPPDATA "Programs\Android Studio\jbr")
    $jdk = $jdkList | Where-Object { $_ -and (Test-Path (Join-Path $_ "bin\java.exe")) } | Select-Object -First 1
    if ($jdk) {
        $env:JAVA_HOME = $jdk
        $env:Path = "$env:JAVA_HOME\bin;$env:Path"
        Write-Host "JAVA_HOME: $env:JAVA_HOME"
    } else {
        Write-Host "JDK 17 not found. Install Microsoft OpenJDK 17 or set JAVA_HOME."
        exit 1
    }
}

& .\gradlew.bat assembleDebug --no-daemon
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$apk = Join-Path $root "app\build\outputs\apk\debug\app-debug.apk"
$out = Join-Path $root "dist"
New-Item -ItemType Directory -Force -Path $out | Out-Null
Copy-Item $apk (Join-Path $out "VpetAoba-debug.apk") -Force
Write-Host "OK: $(Join-Path $out 'VpetAoba-debug.apk')"
Get-Item (Join-Path $out "VpetAoba-debug.apk") | Format-List FullName, Length, LastWriteTime
# 不再另存 VpetMobile-debug.apk，避免同包双份
Remove-Item -Force (Join-Path $out "VpetMobile-debug.apk") -ErrorAction SilentlyContinue
