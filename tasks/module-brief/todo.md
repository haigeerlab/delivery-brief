# Todo: module-brief

- [x] Task 0：提交 Plan 与 todo — 2026-11-19 用户批准 Plan（「批准」）。
- [x] Task 1：Markdown 子集解析 — `brief_markdown.py`：标题、段落（中英文续行拼接）、两层列表（第三层成 `unsupported`）、表格（`\|` 转义）、代码与 mermaid、`<details>` 折叠、其余写法成 `unsupported` 保留原文；行内：行内代码、粗体、链接、引用 `[[path:L起-L止]]` 与写坏的 `badcite`，代码里的引用不算；`citations`、`sections` 帮手。`test_markdown.py` 13 例，实现前模块不存在报错，实现后 49 例全过（两个 Python 版本）。
- [x] Task 2：检查脚本 — `check_brief.py`：六节齐全与顺序；引用在终点提交上存在、行号不越界、写法正确；实跑输出块 ```output O<n>（首行 `$ 命令`）与 `[[out:O<n>]]` 引用；AC 表逐行有证据且覆盖 Spec 的全部编号 AC；「需要你判断的」每条有证据；阅读路线为 3～7 条有序列表且每条有引用；分层 3～7 层；正文提交号须在范围内（允许范围端点、HEAD、终点后的模块提交与 Spec 指纹）；不支持写法、附录内容、多出的节只提醒。范围内补充：Plan 没写实跑输出的标记法，定为 ```output O1 与 `[[out:O1]]`，解析器加 `outref` 与 `output_blocks`（+2 例）。`test_check.py` 18 例，实现前 17 例失败，实现后 69 例全过（两个 Python 版本）。
- [x] Task 3：渲染脚本 — `render_brief.py`：样式取自定稿样张（浅色／深色、手机宽度、Mermaid CDN `mermaid@11.4.1`）；页头（项目、范围与「推断／指定」标签、提交数、文件数与增删、「进行中／已发版」、生成时间）、warnings 与本机工作区不一致提示、附录文件表与提交表全部取自 facts；源文件的一级标题作页面标题、二级标题前的段落作摘要框、第一个 `<details>` 渲染成术语表；引用按 `links` 生成 GitHub 行号链接或 `vscode://` 加文件链接；`[[out:O1]]` 链到实跑输出块；HTML 全部转义，不支持写法原样显示。`test_render.py` 12 例，实现前 12 例失败，实现后通过。范围内补充：检查脚本对没有标题的 mermaid 图出提醒（+1 例）。82 例全过（两个 Python 版本）。
- [x] Task 4：讲解规则与命令文件 — `references/brief-rules.md`（读者与目标、事实从哪来、读取策略、源文件格式模板、六节各写什么、证据硬规则、选图规则、术语小注）；`commands/brief.md`（参数与输出位置、收集事实与退出码处理、先报规模且 `size.diffBytes` 超过 200000 才停下问、实跑只在 `git archive` 临时目录、检查最多两轮、渲染后自动打开与 `--no-open`、前后比对目标项目的 status 与 ref）。`test_rules_doc.py` 6 例：命令里用到的每个参数都在对应脚本 `--help` 里、模板六节与检查脚本一致、阈值与临时目录写法在场；88 例全过。`claude plugin validate .` 通过（目录上架检查缺 LICENSE、README 字数，留到 M1）。
- [x] Task 5：文档 — `docs/facts-schema.md` 加「渲染脚本读哪些字段」一节（页头、提示框、引用链接、附录、页脚，以及检查脚本另读的字段）；`test_schema_doc.py` 仍通过（新段落不是字段表行，不影响比对）。
- [x] Checkpoint 1（report）：完整检查 — 主机 macOS 27.2 arm64：88 例在 Homebrew Python 3.10.7 与系统 Python 3.9.6 各通过一次；`claude plugin validate .` 通过。
- [x] Task 6：真实生成一：spec-guard usage-draft — 两次由没看过样张的新上下文子代理只照命令文件生成（`~/.claude/delivery-brief/sgclone/usage-draft.html`）。
  - 第 1 次（约 16.4 万 token、32 次工具调用、9 分钟）：检查第 2 次通过；报告 12 条说得不清处，其中 2 条是 brief-facts 的解析 bug（AC 续行吞进下一节、入口只去掉前反引号），已修（fa28100，先红后绿）；另补规则：常用字段说明、输出块位置、git 输出可作证据、先分层再写 AC 表、Spec 引用的用途、zsh 安全写法；命令：状态记录文件、临时目录跑测试不用先问、检查次数计法；检查脚本：附录里的输出块判错。
  - 第 2 次（约 17.7 万 token、25 次工具调用、7 分钟）：两次检查 0 错误 0 提醒；又报 12 条措辞与边界不清，已在规则与命令里澄清（输出块可放在讲到它的那一层、多命令输出块、文本交付物的引用、构造输入写明、检查通过后再改也要复检、检查退出码 2、中途停下清理记录文件、`$OUT` 即 `project.name`、先删旧文件再写、遮掉临时路径）。
  - 两次生成前后克隆的工作区与 ref 都不变。
  - 浏览器自验（第 1 次成品）：Mermaid 渲染成功、页头「推断」「已发版」与提示框正确、无横向溢出；第 2 次成品检查通过。
  - 与定稿样张对照（第 2 次成品）：提交数、文件数、增删由脚本生成与样张一致（9、26、+995/−20）；AC1–AC7 全列；五层与样张同构；图 1 张（样张 2 张）。「需要你判断的」13 条：与样张相同 7 条（M1 停点、无独立审查、SKILL.md 超出 Plan、复用私有函数、`unverified` 多出的状态、AC1 没逐字比对、「未验证」分支没测到、`setdefault` 只取第一份）；样张有而这次没有 3 条（没有 python3 时静默跳过、草案目录不可读时预览抛错、add-module 后忘归里程碑不被拦）；这次新发现 4 条（Spec「命令」一节的 `python3 -B -m unittest …/test_module_insert.py` 照写会 ImportError——已在导出目录复现；模板没被检查脚本实际判过；同一模块归两份草案时多报一条；终点后的发版提交）。
  - 对照中发现检查脚本只查「需要你判断的」第一个列表（输出块会把列表断开），已改为查整节全部列表（+1 回归例，先红后绿）；两份真实讲解复检仍 0 错误。
- [x] Task 7：真实生成二：本仓库 brief-facts — 由我照命令文件生成 `~/.claude/delivery-brief/delivery-brief/brief-facts.html`：范围（根）..`ba73323c`、10 个提交、22 个文件 +1792/−0、diff 约 2.4 万 token（未到阈值，只报不问）；实跑在 `git archive` 临时目录（终点提交测试 36 例 OK、`claude plugin validate .` 通过）；第一次检查 0 错误 0 提醒；抽查 16 处引用，1 处行号范围不准（阅读路线第 3 条从辅助函数开始）已改正后复检通过；项目状态前后一致。浏览器自验：Mermaid 1 张渲染成功、浅色与深色、375px 无横向溢出、本机链接与「工作区与终点不一致」提示正常。自验发现并修正：页头「已发版」把 Task 1 文字里的「M1 发版时定」也算成发版——改为只认以「发版」开头的项（+1 回归例，先红后绿，文档同步）；手机上左右布局的图过小，规则补一句节点多时用上下布局。实际耗用：本会话的用量读不到，未记录。
- [x] Checkpoint 2（gate）：最终验收 — 2026-11-19 用户「验收通过」（针对 AC1–AC8 证据、样张对照、改动表与提交表、超出影响面的 brief-facts 修正与拟回告原文）。本仓库无远端，不推送。
- [x] Task 8：反引号括起的引用路径（返工，见 plan「返工（0.3.1）」）— `brief_markdown.INLINE` 最前面加一支 ``[[`路径`(:L起(-L止)?)?]]``（反引号里的路径可含方括号，不含空白与反引号），行号倒置记 `badcite`；旧写法不变。`render_brief.cite` 的链接把 `[`、`]` 编码成 `%5B`、`%5D`，显示文字不变。规则「引用代码」一条与 README 版本记录写新写法，README 去掉这条已知局限；`plugin.json` 0.3.1。
  - 测试：`test_markdown.py` 新增 3 例（含方括号的路径与行号、和旧写法混在一行、单行与倒置、旧写法不变）、`test_check.py` 新增 1 例（终点提交上含方括号的文件：行号在内通过、超出报错）、`test_render.py` 在 GitHub 链接用例里加断言（链接已编码、显示文字未编码）、`test_rules_doc.py` 加规则示例；实现前 4 例失败，实现后 164 例在 Homebrew Python 3.10.7 与系统 Python 3.9.6 各通过一次；`claude plugin validate .` 通过。
  - 改前（`a8c3d0e`）改后渲染三份真实讲解（brief-facts 带交叉核对、next-shadcn 带截图、M1 里程碑页），去掉生成时间后都逐字相同。
  - 实测：把 next-shadcn 那份讲解的副本（scratchpad，不改原产物）里写成代码文字的 `page.tsx` 第 12～19 行改为 ``[[`src/app/auth/sign-in/[[...sign-in]]/page.tsx`:L12-L19]]``，检查 0 错误 0 提醒；改成 L12-L40 时报「行号超出文件行数（19 行）」；渲染出的本机链接为 `…/%5B%5B...sign-in%5D%5D/page.tsx:12`。
- [x] Checkpoint 3（gate）：返工验收与 0.3.1 发版授权 — 2026-11-19 用户「验收通过；1 A；2 A；3 A；4 A」：推送 `main`、在本提交打 `v0.3.1` 并推送、本机升级到 0.3.1、按拟回告原文告诉 ecosystem-lead。
- [x] Task 9：合并命令步骤 — `commands/brief.md`：开头加「少跑几轮」说明；第 1 步改为一个准备块（读规则、跑 facts、删同名旧产物、记项目状态、打印 facts，退出码非 0 时打印并删空 facts）；第 3 步加「分批读」（每批一次调用读多个、输出约 3 万字符以内）与「写完当条消息就检查」；截图的导出、装依赖、起服务合为一块，截完在同一条消息里一次看完；收尾截图、渲染、打开、核对项目状态合为第 5 步一块。`test_rules_doc.py` 新增 `FewerTurnsTest` 6 例，实现前全部失败，实现后命令文件测试 20 例全过。
- [x] Task 10：统计脚本 `dev/run_cost.py` — 从调用命令的那条消息数到下一次调用或会话结束（中途回答停点的用户消息仍算同一次；跳过 `isMeta` 的命令展开），同一条回复拆成多行只算一轮。`dev/test_run_cost.py` 2 例，实现前报错，实现后两个 Python 都过。改前四次：brief-facts 25 轮、交叉核对 22 轮（接在同一会话，首轮上下文 17.4 万）、next-shadcn 提交段 38 轮（缓存读 6196616）、M1 里程碑 25 轮（缓存读 3163957）。
- [x] Task 11：版本 0.3.2 与 README — `plugin.json` 0.3.2；README 版本记录加 0.3.2（并建议在新会话里跑）；`claude plugin validate .` 通过；全部 170 例在 Homebrew Python 3.10.7 与系统 Python 3.9.6 各过一次（另有 `dev/` 2 例）。
- [x] Checkpoint 4（gate）：本机升级插件 — 2026-11-20 用户「同意升级」。`claude plugin marketplace update delivery-brief-marketplace` 后已是 0.3.2（`claude plugin update` 报已是最新）；读回：版本 0.3.2、`installPath` 为 `…/delivery-brief/0.3.2`、`gitCommitSha` 为 `86294c3`；缓存与仓库 `plugins/delivery-brief` 逐文件一致。新开会话或 `/clear` 后加载。之后用户在终端又跑了一遍这两条命令，`claude plugin update` 这次报「从 0.3.1 升到 0.3.2」，与我那次的「已是最新」不一致，原因未查明；再次读回仍只有一条 user 范围记录：0.3.2、`86294c3`，缓存与仓库一致。
- [ ] Task 12：重跑两次实测（AC9）
- [ ] Checkpoint 5（gate）：修订验收与 0.3.2 发版授权

