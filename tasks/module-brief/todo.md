# Todo: module-brief

- [x] Task 0：提交 Plan 与 todo — 2026-11-19 用户批准 Plan（「批准」）。
- [x] Task 1：Markdown 子集解析 — `brief_markdown.py`：标题、段落（中英文续行拼接）、两层列表（第三层成 `unsupported`）、表格（`\|` 转义）、代码与 mermaid、`<details>` 折叠、其余写法成 `unsupported` 保留原文；行内：行内代码、粗体、链接、引用 `[[path:L起-L止]]` 与写坏的 `badcite`，代码里的引用不算；`citations`、`sections` 帮手。`test_markdown.py` 13 例，实现前模块不存在报错，实现后 49 例全过（两个 Python 版本）。
- [x] Task 2：检查脚本 — `check_brief.py`：六节齐全与顺序；引用在终点提交上存在、行号不越界、写法正确；实跑输出块 ```output O<n>（首行 `$ 命令`）与 `[[out:O<n>]]` 引用；AC 表逐行有证据且覆盖 Spec 的全部编号 AC；「需要你判断的」每条有证据；阅读路线为 3～7 条有序列表且每条有引用；分层 3～7 层；正文提交号须在范围内（允许范围端点、HEAD、终点后的模块提交与 Spec 指纹）；不支持写法、附录内容、多出的节只提醒。范围内补充：Plan 没写实跑输出的标记法，定为 ```output O1 与 `[[out:O1]]`，解析器加 `outref` 与 `output_blocks`（+2 例）。`test_check.py` 18 例，实现前 17 例失败，实现后 69 例全过（两个 Python 版本）。
- [x] Task 3：渲染脚本 — `render_brief.py`：样式取自定稿样张（浅色／深色、手机宽度、Mermaid CDN `mermaid@11.4.1`）；页头（项目、范围与「推断／指定」标签、提交数、文件数与增删、「进行中／已发版」、生成时间）、warnings 与本机工作区不一致提示、附录文件表与提交表全部取自 facts；源文件的一级标题作页面标题、二级标题前的段落作摘要框、第一个 `<details>` 渲染成术语表；引用按 `links` 生成 GitHub 行号链接或 `vscode://` 加文件链接；`[[out:O1]]` 链到实跑输出块；HTML 全部转义，不支持写法原样显示。`test_render.py` 12 例，实现前 12 例失败，实现后通过。范围内补充：检查脚本对没有标题的 mermaid 图出提醒（+1 例）。82 例全过（两个 Python 版本）。
- [x] Task 4：讲解规则与命令文件 — `references/brief-rules.md`（读者与目标、事实从哪来、读取策略、源文件格式模板、六节各写什么、证据硬规则、选图规则、术语小注）；`commands/brief.md`（参数与输出位置、收集事实与退出码处理、先报规模且 `size.diffBytes` 超过 200000 才停下问、实跑只在 `git archive` 临时目录、检查最多两轮、渲染后自动打开与 `--no-open`、前后比对目标项目的 status 与 ref）。`test_rules_doc.py` 6 例：命令里用到的每个参数都在对应脚本 `--help` 里、模板六节与检查脚本一致、阈值与临时目录写法在场；88 例全过。`claude plugin validate .` 通过（目录上架检查缺 LICENSE、README 字数，留到 M1）。
- [ ] Task 5：文档
- [ ] Checkpoint 1（report）：完整检查
- [ ] Task 6：真实生成一：spec-guard usage-draft
- [ ] Task 7：真实生成二：本仓库 brief-facts
- [ ] Checkpoint 2（gate）：最终验收
