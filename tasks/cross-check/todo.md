# Todo: cross-check

- [x] Task 0：提交 Plan 与 todo — 2026-11-19 用户批准 Plan（「批准」）。
- [x] Task 1：审查材料脚本 — `crosscheck_material.py`：在输出目录旁建单提交的临时 git 仓库，放 `brief.md`、`facts.json`、`range.diff`、`MATERIAL.md` 与被引用文件在终点提交上的版本（`source/<路径>`）；超过上限（默认 900000 字节）时从最大的被引用文件起换成引用前后各 40 行的带行号窗口（整文件引用取前 80 行）并在 `MATERIAL.md` 注明；仍超限退出 3 并列出各项大小；每次重建。`test_material.py` 7 例，实现前 2 失败 4 报错，实现后 100 例全过（两个 Python 版本），每例比对被讲解项目不变。
- [ ] Task 2：渲染核对记录
- [ ] Task 3：审查模板与命令文件
- [ ] Checkpoint 1（report）：完整检查
- [ ] Task 4：真实交叉核对一次
- [ ] Task 5：M1 发版准备
- [ ] Checkpoint 2（gate）：本机安装插件
- [ ] Task 6：端到端两次
- [ ] Checkpoint 3（gate）：最终验收与发版授权
- [ ] 发版（按 Checkpoint 3 的授权）
