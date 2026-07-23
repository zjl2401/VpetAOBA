# Vpet 桌宠（免费下载）

同人像素桌宠，角色来自《DRAMAtical Murder》（Nitro+CHiRAL）。**非官方作品**。

当前功能尚不完全；更多关注与支持，会带来更多更新与优化。

---

## 网盘分享：对方如何安装（详细）

> 本程序**绿色免安装**：下载 → 解压 → 运行即可，无需安装 Python。

### 你（分享者）要做的

1. 上传整包 zip（见下方「发布包」）到百度网盘 / 阿里云盘 / 夸克等  
2. 开启分享链接（建议「提取码」）  
3. 把链接发给对方，并附一句：

> Windows 用。下载后解压，进文件夹双击「启动.bat」。托盘图标左键生成桌宠。请先看「安装说明.txt」。同人免费，完整剧情请下正版《戏剧性谋杀》。

### 对方（下载者）要做的

1. **下载**网盘里的 zip 到电脑（桌面或「下载」文件夹均可）  
2. **解压**：右键 zip →「全部解压」  
   - 推荐路径：`桌面\Vpet\`  
   - 解压后必须能看到 `Vpet.exe`、`启动.bat`、`_internal`、`bundled`  
3. **启动**：双击 `启动.bat`（或 `Vpet.exe`）  
4. **生成桌宠**：点任务栏/托盘里的 Vpet 图标（**左键**）  
5. **菜单**：在桌宠上**右键**；操作说明按 **F1**  
6. **退出**：托盘右键「退出启动器」，或 `Ctrl+Shift+Q`

### 解压后目录应对得上

```
Vpet/
  Vpet.exe
  启动.bat
  安装说明.txt
  README.md
  _internal/     ← 不要删
  bundled/       ← 语音/音乐/RPG，不要删
```

**不要**只复制一个 `Vpet.exe` 发给别人。

### 常见问题（下载者）

| 现象 | 处理 |
|------|------|
| 双击没反应 | 确认与 `_internal`、`bundled` 在同一层；先退出旧托盘再开 |
| 杀毒拦截 | 加入信任后重试（PyInstaller 打包易误报） |
| 重新下载进度没了？ | 同机进度在 `%LOCALAPPDATA%\Vpet\`，一般换文件夹也不丢 |
| 路径太深打不开 | 解压到桌面或磁盘根目录短路径 |

包内另有简体说明：`安装说明.txt`（适合直接给网盘用户看）。

---

## 请支持正版

完整剧情与官方内容请下载正版《戏剧性谋杀》：

- Steam 搜索：[DRAMatical Murder](https://store.steampowered.com/search/?term=DRAMatical+Murder)
- [Nitro+CHiRAL 官网](https://www.nitrochiral.com/)

本桌宠免费开放，仅供同人欣赏；**不替代正版游戏**。

## 本地存档（同一个人）

- 桌宠数据：`%LOCALAPPDATA%\Vpet\userdata\`
- RPG 存档与历史最高关卡：`%LOCALAPPDATA%\Vpet\rpg\`

面板「好感」显示历史最高 Lv；RPG 标题页与 HUD 显示历史最高关卡。

## 本包包含

- 桌宠模式 / 互动 / 面板 / 本地小游戏 / RPG  
- 语音、音乐资源  

## 本包不含

- 联机邀请对战（未实现）  
- 云端强制按序编号（未部署发号服务时本机分配，可能与他人重复）  

## 源码与反馈

- GitHub：https://github.com/zjl2401/VpetAOBA  
- 开发者：翛然而往  

## 开发者打包

```bat
powershell -ExecutionPolicy Bypass -File .\package_release.ps1 -Shortcut
```
