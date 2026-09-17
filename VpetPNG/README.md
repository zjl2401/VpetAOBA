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
6. **退出**：托盘右键「退出启动器」，或 `Ctrl+Shift+Q`（苍叶；伊得为 `Ctrl+Alt+Q`）

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

个人进度**不在**程序 zip 里，而在本机：

| 路径 | 内容 |
|------|------|
| `%LOCALAPPDATA%\Vpet\userdata\` | 所属人、日记、家园、成就、金币、设置等 |
| `%LOCALAPPDATA%\Vpet\rpg\` | RPG 存档与历史最高关卡 |
| `%LOCALAPPDATA%\Vpet\pet.log` | 运行日志 |

资源管理器地址栏或 Win+R 输入：`%LOCALAPPDATA%\Vpet`

### 恢复「第一次打开」效果

1. 托盘右键「退出启动器」（或 `Ctrl+Shift+Q`；伊得为 `Ctrl+Alt+Q`）  
2. 打开 `%LOCALAPPDATA%\Vpet`  
3. **推荐**：把整个 `Vpet` 文件夹改名为 `Vpet_backup_日期`（可恢复）  
   或直接删除该文件夹（不可恢复）  
4. 再启动程序 → 会新建空存档，等同首次打开  

详细步骤见包内 `安装说明.txt` 第四、五节。

面板「好感」显示历史最高 Lv；RPG 标题页与 HUD 显示历史最高关卡。

## 本包包含

- 桌宠模式 / 互动 / 面板 / 本地小游戏 / RPG / 家园经营（原创，脱离原作）  
- 语音、音乐资源  
- 每天首次打开可领登录礼 1 金币；回忆（画廊 / 留声）在「系统 → 我的」  
- 工作自由/自定义运送；时间显示结束提示；采花可戴头顶  

## 本包不含

- 联机邀请对战（菜单入口提示「尚未开发完全」）  
- AI 对话完整功能（同上）  
- 云端强制按序编号（未部署发号服务时本机分配，可能与他人重复）  
- 个人存档（更新包为干净程序；日记/家园等仍在本机 `%LOCALAPPDATA%\Vpet\`）  

## 源码与反馈

- GitHub：https://github.com/zjl2401/VpetAOBA  
- 开发者：翛然而往  

## 开发者打包

```bat
powershell -ExecutionPolicy Bypass -File .\package_release.ps1 -Shortcut
```

干净更新 zip（无个人记录）会写到桌面：`Vpet_update_日期时间.zip`。