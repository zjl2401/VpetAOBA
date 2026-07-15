# Silent Oath

用地图素材做的小型 2D RPG：大地图、地面/地下双层，支持随机关卡与 DIY 编辑。

## 快速开始

```bash
# 1. 抠图 + 统一尺寸（输出到 assets/）
python process_assets.py

# 2. 启动游戏
python game.py
```

依赖：`pygame`、`Pillow`（已装可忽略）

```bash
pip install pygame Pillow
```

## 特性

- **大地图 + 镜头跟随**：关卡远大于屏幕，视角跟着角色走
- **地面 / 地下**：踩楼梯切换楼层；地下以 brick 为背景、rock 为隔断
- **4 关冒险**：前 3 关找地下金色关卡门；最终关救出目标
- **树木视觉 2 格高**：逻辑仍占 1 格（不可踩）
- **对白框**：使用 `text` 素材
- **DIY 鼠标作图**：底部素材栏点选，左键拖动画地、右键拖擦除；中键/空格拖镜头
- **存档**：冒险中 `F5` 存档；标题 `LOAD SAVE` / `C` 读取；`F9` 快速读档
- **互动**：靠近宝箱/房屋按 `E` 互动（宝箱会打开并留下空箱）

## 操作

| 场景 | 按键 |
|------|------|
| 菜单 | ↑↓ / WS 选择，Enter 确认；C 读档；E 编辑器；L DIY |
| 冒险 | WASD 移动；E 互动；F5 存档；F9 读档；Esc 菜单；R 重开本关 |
| 过关/通关 | Enter 继续 |
| DIY | 点底部素材再拖动画；右键擦；中键/空格拖镜头；滚轮平移；Tab 切层；`S` 起点；`G` 终点；底栏/快捷键：保存·导出·删除·打开；`Ctrl+S` 保存；`Ctrl+Shift+S`/`Ctrl+E` 导出；`Delete`/`Ctrl+D` 删除；`Ctrl+O` 载入；列表里 `Delete`/`X` 删图；`P` 试玩 |

## 文件

- `process_assets.py` — 抠图与统一尺寸
- `game.py` — 游戏主程序
- `assets/` — 处理后的素材（含 `text.png` 对白框）
- `maps/` — DIY 地图 JSON
- `saves/` — 冒险存档（`slot1.json` 等）
