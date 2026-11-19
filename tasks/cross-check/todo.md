# Todo: cross-check

- [x] Task 0：提交 Plan 与 todo — 2026-11-19 用户批准 Plan（「批准」）。
- [x] Task 1：审查材料脚本 — `crosscheck_material.py`：在输出目录旁建单提交的临时 git 仓库，放 `brief.md`、`facts.json`、`range.diff`、`MATERIAL.md` 与被引用文件在终点提交上的版本（`source/<路径>`）；超过上限（默认 900000 字节）时从最大的被引用文件起换成引用前后各 40 行的带行号窗口（整文件引用取前 80 行）并在 `MATERIAL.md` 注明；仍超限退出 3 并列出各项大小；每次重建。`test_material.py` 7 例，实现前 2 失败 4 报错，实现后 100 例全过（两个 Python 版本），每例比对被讲解项目不变。
- [x] Task 2：渲染核对记录 — `render_brief.py --cross-check <json>`：先校验记录（status、backend、model、reportPath、coverage 整数、findings 的 title／verdict／note，incomplete 要有 reason），不合格退出 2 并点名字段；附录加「交叉核对记录」折叠块（后端、模型、覆盖、报告路径、逐条结论），页脚加一行摘要或「交叉核对没有完成：原因」；不给参数时不出任何核对标记，两次渲染去掉时间后逐字相同。`test_render.py` 新增 4 例，实现前 3 例失败，实现后 104 例全过（两个 Python 版本）。
- [x] Task 3：审查模板与命令文件 — `references/cross-check-prompt.md`：只有 `{{project}}`、`{{subject}}` 两个占位，说明材料、请核对的四类（说法不符、引用对不上、漏掉的事实、读不懂），不打分、不给改代码建议、最多 10 条；`commands/brief.md` 加第 4.5 步（没装 delegate 时记 incomplete 并照常渲染、准备材料、只替换占位调用 `delegate:review` 不传后端与模型、读报告且退出 0 不等于通过、逐条核实标 verdict 只改 confirmed、复检、写记录、删材料目录）与 `--cross-check` 参数、规模报告的预计花费、渲染时的 `--cross-check`。`test_rules_doc.py` 新增 3 例（模板只有两个占位、模板不含结论与引导用语、命令流程要素齐全），107 例全过。
- [x] Checkpoint 1（report）：完整检查 — 107 例在 Homebrew Python 3.10.7 与系统 Python 3.9.6 各通过一次；`claude plugin validate .` 通过。
- [ ] Task 4：真实交叉核对一次
- [ ] Task 5：M1 发版准备
- [ ] Checkpoint 2（gate）：本机安装插件
- [ ] Task 6：端到端两次
- [ ] Checkpoint 3（gate）：最终验收与发版授权
- [ ] 发版（按 Checkpoint 3 的授权）
