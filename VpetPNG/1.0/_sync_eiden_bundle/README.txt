伊得仓库更新包（因云端暂无 VpetEidenPet 写权限，先放在苍叶仓库）

【推荐：GitHub Desktop】
1. Desktop 打开 VpetAOBA，分支 cursor/auto-restore-companion-c4c2，Fetch/Pull
2. Show in Explorer，打开本目录旁边的仓库根目录里的：
   eiden-forcequit-cosmetics.patch
3. Desktop 再打开 VpetEidenPet
4. Repository → Open in Command Prompt / PowerShell，执行：
   git apply --reject ..\VpetAOBA\eiden-forcequit-cosmetics.patch
   （路径按你本机两个仓库实际位置改）
5. 回到 Desktop → Changes → Commit → Push origin

若 apply 失败：把苍叶仓库 VpetPNG\1.0\pet.py 不适合直接覆盖伊得
（伊得 pet.py 更大、功能更多）。请回复「已授权伊得仓库」让云端直接推分支。

更新内容：
- 强退：Ctrl+Alt+Q 或 Ctrl+Shift+Q
- 互动 → 表情装扮 ▶：无语/尴尬/疑惑/生气/睡觉Z
