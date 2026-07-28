# VpetMobile（手机试做）

与电脑版 **`VpetPNG/1.0` 完全独立**：本目录是新建的 Android 工程，不会改桌面桌宠代码。

## 本机试做内容

| 模式 | 说明 | 权限 |
|------|------|------|
| **悬浮窗** | 浮在其他 App 上的苍叶；可拖动；点立绘弹出打招呼 / 睡眠 / 站立 | 需要「显示在其他应用上层」 |
| **房间模式** | 普通全屏 App 壳，同一套立绘与动作 | 不需要悬浮权限 |

首期按 [`MOBILE_CHECKLIST.md`](MOBILE_CHECKLIST.md) 逐步复现；家园/RPG/投稿/iOS/云同步等仍靠后。

## 安装 debug APK

1. 用 USB 打开手机「开发者选项 → USB 调试」，或把 APK 拷到手机安装。
2. **现成 debug 包**（本机已打出）：
   - `dist/VpetMobile-debug.apk`（约 6 MB）
   - 或 Gradle 原路径：`app/build/outputs/apk/debug/app-debug.apk`
3. 首次打开 App → 点「打开悬浮窗权限设置」→ 允许「显示在其他应用上层」→ 返回 App →「启动悬浮桌宠」。
4. 切到桌面或其他 App，应能看到悬浮立绘；拖动移动，轻点出菜单。
5. 也可点「打开房间模式」对比普通 App 手感。

国产 ROM 若悬浮不稳定：关闭对该 App 的电池优化 / 允许后台运行。

## 用 Android Studio 打开

1. 安装 [Android Studio](https://developer.android.com/studio) 与 JDK 17。
2. **Open** 本目录 `VpetMobile/`（不要打开整个 `VpetAOBA` 当工程根，除非你刻意要多模块）。
3. 同步 Gradle 后 Run `app`，或 `Build → Build Bundle(s) / APK(s) → Build APK(s)`。

## 命令行构建

需 JDK 17；SDK 可放在本工程 `.android-sdk/`（已在 `.gitignore`），或系统默认 `%LOCALAPPDATA%\Android\Sdk`。

```powershell
cd VpetMobile
# 若 local.properties 中 sdk.dir 指向本机 SDK
.\gradlew.bat assembleDebug
# 或
.\build_debug.ps1
```

产物：`app\build\outputs\apk\debug\app-debug.apk`，脚本还会复制到 `dist\VpetMobile-debug.apk`。

## 资源与进度

- 默认立绘：桌面 `stand.jpg` 等外圈抠图 → `assets/sprites/`  
- 复现进度与电脑版必做对照：[`MOBILE_CHECKLIST.md`](MOBILE_CHECKLIST.md)（核对自 `PRE_VOICE_BASELINE.md` + `FEATURES.md`）  
- 重新导出精灵：`python tools/prepare_default_sprites.py`  
- 逻辑为 Kotlin 轻量壳；**未**整包移植 `pet.py`  
- 桌面版 `VpetPNG/1.0` 保持独立  
