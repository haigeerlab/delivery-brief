# Spec: module-brief

<!-- spec-guard: review pending -->

## 目标

用户输入 `/delivery-brief:brief <模块 id>`（或 `<base>..<head>`），得到一个本机单文件讲解网页，形式以定稿样张为准
（`~/.claude/delivery-brief/spec-guard-plugin/usage-draft.html`）：几分钟看懂这次造了什么、为什么、怎么串起来、哪里要人判断。

样张初稿的教训决定了本模块的做法：3 处失真都出在「模型把数字、结论自己写进页面」。所以**事实由脚本出，叙述由模型写，
引用由脚本核**：页头和附录的数字、文件表、提交表由渲染脚本从 brief-facts 的 JSON 直接生成；模型只写中间的讲解，
里面每条证据用引用标记指向代码行，渲染前由检查脚本逐条核对引用是否真实存在。

对外接口与用法草案 `spec/usage/delivery-brief.md` 一致：入口表第 1、2 行（`/delivery-brief:brief <模块 id>`、`<base>..<head>`），
U1 的前半（不含 `--cross-check`，那是 cross-check 模块）。

给谁用：在关键节点想看懂一个模块的用户本人；事后补看以前的模块也一样。

## 假设

1. **命令**：`/delivery-brief:brief <模块 id | base..head> [--project <dir>] [--no-open]`，`--project` 缺省为当前项目根目录。只做 Claude Code。
2. **流程**（命令文件 `commands/brief.md` 规定，模型照做）：
   1. 跑 `brief_facts.py` 取事实；把范围、来源（推断还是指定）、warnings 和规模先告诉用户；
   2. 规模超过阈值时停下问是否继续：按 diff 规模判断（`size.diffBytes ÷ 4` 超过 5 万，约 20 万字节），不用 `size.estimatedTokens`
      （它把被改文件全文算进去，实测高估约 10 倍）；没超过只报不问；
   3. 按讲解规则读代码、写讲解源文件；需要实跑输出时，只在 `git archive <终点>` 导出的临时目录里跑，不在项目里跑；
   4. 跑检查脚本；不通过就按报告改，最多改两轮，仍不通过就停下，把检查报告给用户；
   5. 渲染成 HTML，给出路径并自动用默认浏览器打开；`--no-open` 时不打开，没有 `open` 命令的系统只给路径。
3. **讲解源文件用 Markdown 子集，由渲染脚本出 HTML**，而不是让模型直接写 HTML。理由：样式、深浅色、手机宽度、页头附录这些
   固定部分由脚本保证一致；模型输出更短；引用可以被机器核对。支持的子集：标题、段落、有序／无序列表（两层）、表格、
   代码块、`mermaid` 代码块、行内代码、粗体、链接、`<details>` 折叠。不支持的写法原样当文本显示，检查脚本报出来。
4. **引用标记**：`[[路径:L起-L止]]` 或 `[[路径]]`。渲染时按 brief-facts 的 `links` 生成链接：GitHub 时链到终点提交的行号，
   本机时链到文件（`vscode://file/<绝对路径>:<起始行>` 与文件路径各给一个）。检查脚本要求：文件在终点提交上存在、行号不超出文件行数。
5. **固定结构**：讲解源文件必须有这六节（标题固定，渲染时编号）：`为什么改`、`产出清单`、`分层讲改动`、`阅读路线`、
   `需要你判断的`、`附录`。前五节内容由模型写，「讲法是活的」——分几层（3～7）、配不配图、清单分哪几类由内容和项目类型定；
   `附录` 只写一行占位，文件表与提交表由渲染脚本生成。页头（项目、范围、来源标签「推断」或「指定」、提交数、文件数与增删、
   发版或进行中状态、生成时间）与术语小注的位置也由脚本生成，术语内容由模型写。
6. **检查脚本 `check_brief.py`**（只做机器能可靠判断的）：六节都在且顺序对；每个引用可解析；「为什么改」里每个 AC 的证据格
   至少有一个引用或实跑输出块；「需要你判断的」每一条至少有一个引用或实跑输出块；「阅读路线」是有序列表、条目数 3～7 且每条有引用；
   「分层讲改动」的层数（三级标题）在 3～7；正文里出现的提交号前缀都在本次范围内；不支持的 Markdown 写法列为提醒。
   不检查叙述是否正确——那是 cross-check 模块与用户的事。
7. **讲解规则**写在插件的 `references/brief-rules.md`，命令运行时读它：六问各写什么；证据硬规则（只引用测试断言、代码行或实跑输出，
   不照抄 Spec 原话）；读取策略（先读 diff 与 facts，再按需读文件片段，不整读大文件——usage-draft 一次估算约 25 万 token，主要是整读大文件）；
   选图规则（据用户的《技术图表选型指南》：先定读者的问题再选图、一图一问、标题写结论、5～12 个节点、一种箭头一种含义、
   直线步骤用编号列表不画图、整页两三张够）；「需要你判断的」只摆事实不打分。
8. **输出位置**：`~/.claude/delivery-brief/<项目目录名>/<模块 id>.html`，讲解源文件 `<模块 id>.md` 放在旁边；`--range` 时文件名用
   `<base 前 8 位>..<head 前 8 位>`。同名已存在时覆盖（讲解页不需要维护，可随时重生成）。不写被讲解项目的任何文件。
9. **页面外观**照定稿样张：本机字体、浅色／深色、手机宽度无横向滚动、Mermaid 从 CDN 加载（`mermaid@11.4.1`，需要联网），
   没有其他外部依赖。
10. **少跑几轮**（2026-11-19 修订）：每多一轮对话，模型都要把整个上下文重读一遍；实测一次讲解约 25～38 轮，每轮重读的固定上下文约 9.6 万 token，
    这部分约占花费的四成。所以命令文件把**前后不依赖彼此结果**的步骤合进一次调用：读讲解规则与收集事实、记项目状态合为一次；
    读代码先按 facts 定好要读的文件，再分批一次读多个（每批输出控制在约 3 万字符以内，超了会被落盘、反而多一轮）；
    写讲解源文件与检查放在同一条消息里；截图的导出、装依赖、起服务合为一次，截完一次看完所有截图；渲染、打开、核对项目状态合为一次。
    讲解读什么、写什么、证据规则、停点都不变。

## 命令

```text
python3 -B -m unittest discover -s plugins/delivery-brief/tests
python3 -B plugins/delivery-brief/scripts/check_brief.py --facts <facts.json> --source <brief.md>
python3 -B plugins/delivery-brief/scripts/render_brief.py --facts <facts.json> --source <brief.md> --out <brief.html>
/delivery-brief:brief usage-draft --project <spec-guard 克隆>
claude plugin validate .
```

## 项目结构

```text
plugins/delivery-brief/commands/brief.md           # 命令：流程、何时停下问、出错怎么办
plugins/delivery-brief/references/brief-rules.md   # 讲解规则（模型运行时读）
plugins/delivery-brief/scripts/brief_markdown.py   # Markdown 子集解析（检查与渲染共用）
plugins/delivery-brief/scripts/check_brief.py      # 检查脚本
plugins/delivery-brief/scripts/render_brief.py     # 渲染脚本（含页面外壳与样式）
plugins/delivery-brief/tests/                      # 解析、检查、渲染的单元测试
```

## 测试策略

- 解析、检查、渲染三个脚本先写测试再实现：每条检查规则一个反例；渲染输出里页头与附录的数字逐项等于 facts；引用在 GitHub／本机两种
  链接下都拼对；不支持的写法原样显示且被检查脚本提醒；HTML 转义（代码里的 `<`、`&` 不破坏页面）。
- 命令本身由模型执行，没法单元测试，用两次真实生成验收：
  1. spec-guard 克隆上的 `usage-draft`：检查脚本通过；在浏览器里看两张以上的 Mermaid 图渲染成功、手机宽度无横向溢出；
     把定稿样张里的事实（提交数、文件数、AC、「需要你判断的」里的各条）逐项对照，记下多了什么、少了什么；
  2. 本仓库的 `brief-facts`（本机链接、没有用法草案外的入口）：同样检查与浏览器自验。
- 两次生成都记录规模估算与实际耗用（从会话用量读得到就记，读不到写明）。

## 边界

- Always：页头与附录的数字只由渲染脚本从 facts 生成；每条证据带引用；实跑只在导出的临时目录；不写被讲解项目；输出只在
  `~/.claude/delivery-brief/`；生成前报规模。
- Ask first：超过阈值继续生成；讲解源文件检查两轮仍不过时是否照样渲染；任何要联网的步骤（`gh` 之外）；
  在项目目录里跑命令。
- Never：给代码质量打分；把模型写的数字放进页头或附录；在被讲解项目里写文件、改 git 状态或跑会写文件的命令；
  替代 delegate 的独立审查（`--cross-check` 属 cross-check 模块）。

## 成功标准

- AC1：`/delivery-brief:brief <模块 id>` 与 `/delivery-brief:brief <base>..<head>` 都能走完假设 2 的流程；生成前先报范围、来源、
  warnings 与规模，超过阈值停下问。
- AC2：渲染脚本把讲解源文件与 facts 渲染成单文件 HTML：页头与附录（文件表、提交表）的每个数字等于 facts；样式照定稿样张，
  浅色／深色都可读，375px 宽度无横向溢出。
- AC3：引用标记在 GitHub 与本机两种链接下都生成正确链接；文件不存在或行号越界时检查脚本报错并点名。
- AC4：检查脚本按假设 6 的每条规则报错（每条都有反例测试），报告逐条写明位置；只是提醒的项不判失败。
- AC5：`references/brief-rules.md` 写全假设 7 的内容；命令文件写全假设 2 的流程与停点。
- AC6：实跑只在 `git archive` 导出的临时目录进行；两次真实生成前后，被讲解项目的工作区与 ref 不变。
- AC7：两次真实生成（spec-guard `usage-draft`、本仓库 `brief-facts`）检查通过、浏览器自验通过；`usage-draft` 与定稿样张的事实
  对照结果写进验收材料。
- AC8：`claude plugin validate .` 通过；全部单元测试在系统 Python 3.9 与 Homebrew Python 各过一次。
- AC9（2026-11-19 修订）：命令文件按假设 10 合并步骤（测试守护合并后的命令块）；在新会话里用安装后的版本重跑两次此前实测过的讲解，
  轮数与重读量都下降：提交段 `2331c322..cacd0d02`（next-shadcn，带截图，原 38 轮）不超过 25 轮，本仓库 `--milestone M1`（原 25 轮）不超过 18 轮；
  两次检查都 0 错误，讲解的节与证据规则不变。

## 文档建议

- 本模块自己的：`references/brief-rules.md` 既给模型读，也是讲法的规格，以后改讲法以它为准；`docs/facts-schema.md` 补一句
  「渲染脚本读哪些字段」。README 仍等 M1 发版（cross-check 完成后）一起写。

## 待定问题

- 无。Q1、Q2 已于 2026-11-19 由用户定为 A（「批准；Q1 A；Q2 A」），写进假设 1、2：diff 规模超过约 5 万 token 才停下问；生成后自动打开，
  `--no-open` 关掉。

## 变更记录

- 2026-11-19：新增假设 10「少跑几轮」与 AC9（用户要求降低 token 花费，调研后选定「减少轮数」）。不改讲解内容、证据规则与停点。
