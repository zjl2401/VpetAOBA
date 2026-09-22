# VpetMobile（双端手机版 · 1C + KMP）

与电脑版 **`VpetPNG` 完全独立**：本目录是 Android + 共享 KMP + iOS 房间壳，**不为手机需求大改桌面**。

## 架构

| 模块 | 说明 |
|------|------|
| `:shared` | Kotlin Multiplatform：`FoodCatalog` / `RhythmGrades` / `PetSession` / `Shared*Store` / `PlatformClock|Storage|Audio` |
| `:app` | Android UI + `PetOverlayService` 悬浮窗 |
| `iosApp/` | SwiftUI **房间模式**（无系统级悬浮）；Mac 上链入 `VpetShared.framework` |

对等范围与跳过项见 [`MOBILE_CHECKLIST.md`](MOBILE_CHECKLIST.md)（**双端基线 = 该清单 MVP**）。

## Android：安装 debug APK

1. USB 调试或侧载 APK。
2. 现成包：`dist/VpetMobile-debug.apk`（或 `app/build/outputs/apk/debug/app-debug.apk`）。
3. 认主 →「显示在其他应用上层」→「启动悬浮桌宠」；也可「打开房间模式」。

```powershell
cd VpetMobile
# 推荐直接用已解压的 Gradle（wrapper 若反复拉 zip 可改用）：
#   %USERPROFILE%\.gradle\wrapper\dists\gradle-8.7-bin\*\gradle-8.7\bin\gradle.bat
.\gradlew.bat :shared:assembleDebug :app:assembleDebug
# 或
.\build_debug.ps1
```

需 JDK 17；`local.properties` 的 `sdk.dir` 可指向本仓 `.android-sdk/`。

## iOS：房间壳

见 [`iosApp/README.md`](iosApp/README.md)。Windows 仅维护 Swift 源；真机构建在 Mac。

手测：认主 → 房间 → 模式 / 喂食 / 家园 / 小游戏 / 工具（与清单对照）。

## 明确不做（本阶段）

- 打字、背单词、天气、网易云云端歌单
- 桌面「相遇友情 / selecttalk」移植
- Flutter 重写
- iOS 全局悬浮在任意 App 上

## 资源

- 立绘：`assets/sprites/`；导出脚本 `python tools/prepare_default_sprites.py`
- 复现进度：[`MOBILE_CHECKLIST.md`](MOBILE_CHECKLIST.md)
