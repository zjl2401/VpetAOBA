# VpetMobile iOS（房间模式首版）

与 Android 共用 `../shared`（Kotlin Multiplatform → `VpetShared` framework）。  
**系统不允许**等价于 Android `SYSTEM_ALERT_WINDOW` 的全局悬浮；首版只做 **App 内房间模式**。

## 前置

- macOS + Xcode 15+
- JDK 17（编 shared）
- 真机需 Apple Developer 账号签名

## 编译共享框架

在 `VpetMobile/` 根目录（需在 Mac 上）：

```bash
./gradlew :shared:linkDebugFrameworkIosSimulatorArm64 -Pvpet.enableIos=true
# 或真机
./gradlew :shared:linkDebugFrameworkIosArm64 -Pvpet.enableIos=true
```

产物一般在：

`shared/build/bin/iosSimulatorArm64/debugFramework/VpetShared.framework`

## 打开工程

1. Xcode → **File → New → Project → App**（或用本目录源文件自建 target `VpetMobile`）
2. 把 `iosApp/VpetMobile/**` 源码加入 target
3. **General → Frameworks**：Add `VpetShared.framework`，Embed & Sign
4. Bundle ID / Team 换成你的
5. `Info.plist` 可用 `Resources/Info.plist`

Windows 上可先改 Swift 源；**无法**在本机出 IPA。无 framework 时 `MockPetSession` 可独立跑 UI。

## 手测路径（对等 MOBILE_CHECKLIST MVP）

认主 → 进房间 → 切模式 → 面板喂食 → 家园工具 → 游戏简版 → 番茄/秒表。

## 已知限制

- 无系统级悬浮 / 无 Android 悬浮权限流
- 精灵与语音需从 Android `assets` 瘦包同步
- 打字 / 背单词 / 天气 / 云端歌单：跳过（与 Android 同）
