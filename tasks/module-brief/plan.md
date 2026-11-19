# Plan: module-brief

<!-- spec-guard: review approved -->

依据 [`spec/module-brief.md`](../../spec/module-brief.md)（2026-11-19 用户在本会话批准：「批准；Q1 A；Q2 A」，提交 `91d4ff2`）。
分支 `main`（本仓库没有远端），串行，在本会话做。本模块不发版：M1 还差 cross-check，发版在 cross-check 验收后。

## Overview

先做三个确定性的脚本（Markdown 子集解析 → 检查 → 渲染），每个先写失败的测试再实现；再写讲解规则与命令文件；
最后做两次真实生成验收，其中 spec-guard `usage-draft` 那次交给一个**没看过样张的新上下文子代理**只照命令文件做，
检验命令文件本身够不够用；我负责检查、浏览器自验与和样张对照。

## Architecture Decisions

1. **三个脚本共用一个解析器**：`brief_markdown.py` 把讲解源文件解析成块列表（标题、段落、列表、表格、代码、mermaid、折叠块）
   与行内片段（文字、行内代码、粗体、链接、引用），检查与渲染都只读这棵树，不各自解析，避免两边对同一写法理解不同。
   不支持的写法作为 `unsupported` 块保留原文。
2. **引用标记** `[[path:L12-L30]]`、`[[path:L12]]`、`[[path]]`：解析器只认格式；检查脚本用 `git show <终点>:<path>` 核对存在与行数
   （复用 `facts_git`）；渲染脚本按 `facts.links` 拼链接：GitHub 为 `base + path + #L12-L30`，本机为 `vscode://file/<绝对路径>:12`
   加一个文件路径文字。链接文字是 `path:12-30`。
3. **页头、附录、样式由 `render_brief.py` 生成**：页面外壳（CSS 令牌、深色、手机宽度、Mermaid CDN `mermaid@11.4.1`）从定稿样张提取进脚本；
   页头取 `project`、`range`（来源标「推断」或「指定」、进行中标明）、`totals`、`commits` 数、`module.todo.atHead`（有「发版」类勾选则写已发版）、
   生成时间；附录取 `files` 与 `commits`。讲解源文件里的 `附录` 一节只放占位。术语小注是讲解源文件第一个 `<details>` 块，渲染到页头下。
4. **检查脚本退出码**：0 通过（可有提醒）、1 有错误、2 参数错；报告每行 `error|warn <位置>：<说明>`，位置写「节名 第 n 项」或行号。
   命令文件按报告修改，最多两轮。
5. **命令文件只写流程，不写讲法**：讲法全在 `references/brief-rules.md`，命令文件开头要求先读它。规模阈值、自动打开、
   实跑在 `git archive` 临时目录、出错停下的几种情况都写在命令文件里。
6. **真实生成用新上下文子代理做第一次**：本会话已经看过样张，自己生成会不自觉照抄样张而不是读代码；交给 general-purpose 子代理，
   提示词只给命令、参数与「照 `commands/brief.md` 做」，不给样张。子代理产出后由我跑检查、浏览器自验、逐项对照样张。

## Task List

### Task 0：提交 Plan 与 todo

- 验证：verify-artifacts 0 失败。

### Task 1：Markdown 子集解析（`brief_markdown.py`）

- 用例：六种块各一例；两层列表、有序列表；表格里的竖线转义与引用；代码块里的 `[[...]]` 不当引用；`<details>` 块；不支持的写法
  （如 HTML 标签、三层列表）成为 `unsupported`；引用三种写法与非法写法。
- 验证：先红后绿。

### Task 2：检查脚本（`check_brief.py`）（AC3、AC4）

- 用例（夹具仓库 + 真实 facts）：六节缺失、顺序错；引用文件不存在、行号越界；AC 证据格没有引用也没有实跑块；
  「需要你判断的」某条没有证据；阅读路线不是有序列表、条数越界、某条没引用；分层不在 3～7；提交号不在范围内；
  不支持写法只提醒、退出 0；合格源文件退出 0。
- 验证：先红后绿，每条规则一个反例。

### Task 3：渲染脚本（`render_brief.py`）（AC2、AC3）

- 用例：页头与附录的每个数字等于 facts（提交数、文件数、增删、逐文件行、提交表）；「推断」「指定」「进行中」「已发版」四种标签；
  GitHub 与本机两种引用链接；代码与文字里的 `<`、`&` 被转义；mermaid 块原样进 `<pre class="mermaid">`；不支持写法原样显示；
  输出是单个文件、只引用 CDN 上的 mermaid。
- 验证：先红后绿。

### Task 4：讲解规则与命令文件（AC1、AC5）

- 文件：`references/brief-rules.md`、`commands/brief.md`。
- 内容：Spec 假设 2 的流程与停点（diff 超过约 5 万 token 停下问；`--no-open`；实跑只在 `git archive` 临时目录；检查两轮不过停下问）；
  假设 7 的讲法、证据硬规则、读取策略与选图规则；讲解源文件的格式示例（六节、引用、术语块、实跑输出块的写法）。
- 验证：`claude plugin validate .` 通过；规则里出现的脚本参数与脚本 `--help` 一致（测试比对）。

### Task 5：文档

- 文件：`docs/facts-schema.md` 补「渲染脚本读哪些字段」一节。
- 验证：`test_schema_doc.py` 仍通过。

### Checkpoint 1（report）：完整检查

- 全部单元测试在系统 Python 3.9.6 与 Homebrew Python 各跑一次；`claude plugin validate .`。

### Task 6：真实生成一：spec-guard `usage-draft`（AC1、AC6、AC7）

- 新上下文子代理照 `commands/brief.md` 对 spec-guard 临时克隆生成（`--no-open`，由我来打开）；生成前后比对克隆的工作区与 ref。
- 我：跑检查脚本；浏览器自验（两张以上 Mermaid 渲染成功、浅色与深色、375px 无横向溢出、抽查 5 个引用链接打开后行号对得上）；
  与定稿样张逐项对照（提交数、文件数、AC、产出清单各项、「需要你判断的」各条），把多出、缺少、不一致的写进 todo。
- 子代理暴露出命令文件或规则缺的东西，在本任务里补，补完再生成一次。

### Task 7：真实生成二：本仓库 `brief-facts`

- 由我照命令文件生成（本机链接、无界面）；检查脚本与浏览器自验同上；记录规模报告与实际耗用（读得到就记，读不到写明）。

### Checkpoint 2（gate）：最终验收

- 呈现：AC1–AC8 证据、两份讲解页的路径与截图、和样张的对照结果、改动表、提交表、偏离计划处。不含推送（没有远端）。

## Files likely touched

- 新增：`plugins/delivery-brief/scripts/{brief_markdown,check_brief,render_brief}.py`、`plugins/delivery-brief/commands/brief.md`、
  `plugins/delivery-brief/references/brief-rules.md`、`plugins/delivery-brief/tests/{test_markdown,test_check,test_render,test_rules_doc}.py`。
- 修改：`docs/facts-schema.md`。
- 记录：本 Plan、`tasks/module-brief/todo.md`。
- 仓库外：讲解页写到 `~/.claude/delivery-brief/`（Spec 规定的输出位置）；实测用 scratchpad 里的 spec-guard 临时克隆。
- 新增依赖、锁文件：无。不改全局配置、不安装插件：`/delivery-brief:brief` 的斜杠命令接线到 M1 发版、你同意安装时再端到端跑；
  本模块的真实生成照命令文件逐步执行。

## 风险

- **命令文件不够用**：模型照着做仍跑偏。缓解：第一次交给没看过样张的子代理，暴露的缺口在 Task 6 里补并重跑。
- **Mermaid 语法错脚本查不出**：只能浏览器自验；规则里要求图少而简单，自验时逐张看。
- **规则遵守有随机性**：同一模块两次生成讲法会不同，这是「讲法是活的」的一部分；检查脚本守住结构和引用，叙述正确性留给 cross-check 和你。
- **真实生成的花费**：一次讲解要读 diff 和若干文件片段；本会话上下文已经很长，建议在 Task 0 之后 `/compact`。子代理那次在它自己的上下文里花。
- **斜杠命令没有端到端跑过**：本模块只验证命令文件内容与 `validate`；接线问题要到安装后才暴露，M1 发版前补一次端到端。

## 预先声明

- Public paths: 无
- Dependencies: 无
- Configs: 无
- Patches: 无

## 返工（0.3.1）：路径含方括号的引用

2026-11-19 ui-screenshots 实测 Next.js 项目时发现：引用写法 `[[路径…]]` 不允许路径里有 `[`、`]`，所以 `src/app/auth/sign-in/[[...sign-in]]/page.tsx`
这类可选捕获路由的文件没法引用（`brief_markdown.CITE`）。这是本模块已批准范围里的缺口（讲解要能引用范围内的任何文件），按 spec-guard「返工与小模块」规则在本模块返工，不开新模块、不重新交审。

### Task 8：反引号括起的引用路径

- 文件：`scripts/brief_markdown.py`、`scripts/render_brief.py`、`references/brief-rules.md`、`tests/test_markdown.py`、`tests/test_check.py`、`tests/test_render.py`。
- 做法：新增写法 ``[[`路径`]]``、``[[`路径`:L12]]``、``[[`路径`:L12-L30]]``，反引号里的路径可以含 `[`、`]` 与空格以外的字符；不加反引号的旧写法不变。
  渲染链接时把路径里的 `[`、`]` 编码成 `%5B`、`%5D`，其他路径的链接不变。
- 用例：解析出路径与行号（含和旧写法混在一行）；检查脚本在终点提交上核对含方括号的文件与行号（存在通过、行号超出报错）；渲染出的链接已编码；旧写法的解析与渲染不变。
- 验证：先红后绿；用改前改后的渲染脚本渲染真实模块讲解逐字比对；对 next-shadcn 那段提交的讲解改用新写法引用 `page.tsx`，检查通过。

### Checkpoint 3（gate）：返工验收与 0.3.1 发版授权

## 修订（0.3.2）：少跑几轮

2026-11-19 用户反映讲解太费 token。调研四次真实运行的会话记录：每轮重读的固定上下文约 9.6 万 token，乘以 25～38 轮约占花费的四成；
HTML 排版由脚本做，不花 token。用户选定只做「减少轮数」（Spec 假设 10、AC9）。超出原批准范围，Spec 与本 Plan 改为待批准重新交审。

### Task 9：合并命令步骤

- 文件：`commands/brief.md`、`tests/test_rules_doc.py`。
- 做法：
  - 开头一个「准备」命令块：读讲解规则、跑 `brief_facts.py`、记项目状态、打印 facts，一次调用做完；退出码非 0 的处理不变。
  - 第 3 步：先按 facts 列出要读的 diff 与片段，分批读，每批一次调用读多个文件，每批输出约 3 万字符以内。
  - 写讲解源文件后，同一条消息里接着跑检查。
  - 截图：导出、装依赖、起服务合为一次；截完在同一条消息里看完所有截图；收尾与渲染合为一次。
  - 第 5 步：渲染、打开、核对项目状态合为一次。
  - 里程碑页、交叉核对的流程照旧，只套用上面的合并方式。
- 用例：「准备」块里同时有读规则、`brief_facts.py`、记状态；第 3 步写明分批与每批上限；写源文件与检查写明在同一条消息；
  渲染块里同时有 `render_brief.py`、`open` 与状态比对；原有的安全删除、参数在 `--help` 里等测试照常通过。
- 验证：先红后绿；`claude plugin validate .`；两个 Python 版本全部测试。

### Task 10：统计脚本

- 文件：`dev/run_cost.py`（新，不进插件目录）、`tests/test_run_cost.py`。
- 做法：读一个会话记录，从调用 `/delivery-brief:brief` 的那条消息算到下一条用户消息，输出轮数、首轮上下文、缓存读写、输出 token、工具结果字符数。
- 用例：用构造的会话记录核对各项计数（同一条回复拆成多行时只算一次）。验收用它算改前四次与改后两次的数。

### Task 11：版本 0.3.2 与 README

- README 版本记录加 0.3.2；`plugin.json` 0.3.2。

### Checkpoint 4（gate）：本机升级插件

- 停下问你；升级后读回版本与提交号，逐文件比对缓存。

### Task 12：重跑两次实测（AC9）

- 你在新会话分别运行 `/delivery-brief:brief 2331c322..cacd0d02 --project ~/Documents/gs/next-shadcn-dashboard-starter` 与
  `/delivery-brief:brief --milestone M1 --project ~/Documents/haigeerlab/delivery-brief`；我用 `dev/run_cost.py` 算改前改后的数，核对检查结果与被讲解项目不变。

### Checkpoint 5（gate）：修订验收与 0.3.2 发版授权

