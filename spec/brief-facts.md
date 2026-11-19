# Spec: brief-facts

<!-- spec-guard: review approved ddc1119ddde6 -->

## 目标

给后面所有讲解模块一份**可核对的事实底稿**：把「模块 id」或「任意一段提交」解析成确定的提交范围，收集讲解要用的事实，
输出 JSON。讲解页里凡是数字、文件、提交、AC、勾选状态，都从这里来，不靠模型回忆或概括（样张初稿的 3 处失真都出在这里）。
同时搭好插件骨架，让后面的模块直接往里加命令。

本模块只读、不调用模型、不生成网页。它是用法草案里的基础设施模块：入口 `brief_facts.py` 由 `/delivery-brief:brief`（module-brief）
在内部调用，也可以单独跑来核对范围。对外接口与用法草案 `spec/usage/delivery-brief.md` 一致（入口表第 3 行，M1）。

给谁用：module-brief、milestone-brief 等后续模块；以及想核对「这次讲的是哪段提交」的用户。

## 假设

1. **仓库布局照 delegate-plugin**：根目录 `.claude-plugin/marketplace.json`，插件在 `plugins/delivery-brief/`
   （`.claude-plugin/plugin.json`、`commands/`、`scripts/`）。第一版只做 Claude Code，不出 `.codex-plugin/`。
   本模块只建骨架和脚本，不加命令；版本号在 M1 发版时定（预计 0.1.0），本模块不发版。
2. **Python 3 标准库**，兼容 macOS 自带的 3.9，不装依赖。
3. **命令行**：
   ```text
   brief_facts.py --project <dir> (--module <id> | --range <base>..<head>) [--offline]
   ```
   stdout 输出一个 JSON 对象；退出码 0 成功、2 参数错、3 解析不出范围（模块不在能力图上、找不到提交）、4 git 出错。
   出错时 stderr 一行中文说明，不抛堆栈。
4. **模块范围的推断规则（不改 spec-guard）**。实测 spec-guard 0.87.0 现有只读接口不够：`declaredScope` 只给 Plan 批准时的
   提交（`approvedCommit`），`mapView` 只给勾选次数和时间，都没有提交列表和终点。所以按 spec-guard 已公开的文件约定推断：
   - **起点**：沿 HEAD 的历史，第一个改动 `spec/<id>.md` 或 `tasks/<id>/` 的非合并提交；
   - **终点**：把 todo 里最后一个已勾选的 `（gate）` 检查点从 `[ ]` 改成 `[x]` 的那个提交（通常是「最终验收通过」）。
     之后的发版收尾提交（也会改 todo）不算进来。还没有任何 gate 勾上时，终点取最后一个改动该模块文件的提交，并标 `inProgress: true`；
   - **范围**：`起点^..终点` 之间的非合并提交；其中改动了别的模块 `spec/<其他>.md` 或 `tasks/<其他>/` 的提交照样列出，但进 `warnings`。
   - 用 spec-guard 自己的两个已完成模块实测过：usage-draft 推出 `273faa86`→`70c3b750`（9 个提交），map-extra-columns 推出
     `c9ee3329`→`e0cfa90a`（6 个提交），都与人工核对一致。
   - 输出里 `range.source` 写明 `inferred-spec-guard` 或 `explicit`。推断不如权威数据可靠，所以批准后我经 ecosystem-lead 请 sg-coord
     考虑补一个只读接口（给出模块的提交列表与验收提交）；对方补了以后改用接口，规则保留作后备。
5. **收集的事实**（JSON 顶层字段）：
   - `project`：根目录、目录名、HEAD；
   - `range`：`base`、`head`、`source`、`inProgress`、推断依据（起点和终点各是哪个提交、为什么）；
   - `commits`：每个提交的 sha、标题、日期、改了哪些文件；
   - `files`：`git diff --numstat -M` 的逐文件结果（状态 A/M/D/R、增、删、是否二进制），附合计；
   - `module`（只在 `--module` 时）：能力图里的职责与依赖、Spec 路径与批准标记、AC 列表（`AC<n>` 编号 + 原文）、
     todo 各项（文字、是否勾选、`gate`／`report`／普通任务）。todo **同时给终点提交和 HEAD 两份**：样张里「发版」一项在标签上
     未勾、在 main 上已勾，两份都要有才说得清；
   - `usageDraft`（只在 `--module` 且有 `spec/usage/` 时）：本模块属于哪份草案的哪个里程碑、归它的入口。按 spec-guard 模板的
     节名与表头自己解析，不调用 spec-guard 的脚本（那不在它的对外接口里）；
   - `links`：代码链接怎么生成。GitHub 公开仓库、并且终点提交已在远端时，用 `https://github.com/<owner>/<repo>/blob/<终点 sha>/`；
     否则用本机文件路径，并注明本机工作区与终点提交是否一致。判断「公开」用 `gh api`；`--offline` 或 `gh` 不可用时一律本机链接，
     原因写进 `links.reason`；
   - `size`：文件数、增删行、diff 字节数、范围末端被改文件的总字节数，以及按「字节 ÷ 4」估的读取 token 数（只是量级，用于生成前提示）；
   - `warnings`：推断范围、混入别的模块的提交、终点未推送、读不到某个文件等。
6. **只读**：不写被讲解项目的任何文件，不 `fetch`、不改 ref；唯一的网络访问是可选的 `gh api` 查仓库可见性和终点提交是否在远端。

## 命令

```text
python3 -B -m unittest discover -s plugins/delivery-brief/tests
python3 -B plugins/delivery-brief/scripts/brief_facts.py --project <spec-guard 克隆> --module usage-draft --offline
claude plugin validate .
```

## 项目结构

```text
.claude-plugin/marketplace.json
plugins/delivery-brief/.claude-plugin/plugin.json
plugins/delivery-brief/scripts/brief_facts.py      # 命令行与 JSON 输出
plugins/delivery-brief/scripts/facts/              # 按需拆分：git 读取、spec-guard 文件解析、链接判断
plugins/delivery-brief/tests/                      # unittest，夹具为临时 git 仓库
README.md                                          # 只写一段「开发中」说明，完整说明等 M1
```

## 测试策略

- 先写测试并确认失败，再实现。
- 夹具：测试里用临时目录现建 git 仓库，按 spec-guard 约定造能力图、Spec、todo 和用法草案，覆盖：完成的模块、进行中的模块、
  验收后还有发版提交、混入别的模块的提交、有合并提交、没有 spec-guard 的普通仓库。
- 只读守护：跑完后 `git status --porcelain`、全部 ref 与跑之前一致。
- 实测：对 spec-guard 仓库的临时克隆（远端 main `291a0c74`）跑 usage-draft 与 map-extra-columns，起止提交、提交数与逐文件增删
  和人工核对一致（结果记进 todo）。
- 变异：去掉「终点取最后一个已勾 gate」改成「最后一次改 todo」，测试要变红（发版收尾提交会被算进来）。

## 边界

- Always：只读；标准库；先红后绿；推断出的范围一律标来源；出错给一行中文说明。
- Ask first：改 spec-guard 或请它改接口之外的行为；加第三方依赖；`gh api` 之外的网络访问；生成网页或调用模型（属 module-brief）。
- Never：写被讲解项目的文件或 git 状态；在 spec-guard 仓库里改任何东西；把推断的范围当作权威数据而不标来源。

## 成功标准

- AC1：`--range <base>..<head>` 输出的提交与逐文件增删，和 `git rev-list --no-merges`、`git diff --numstat -M` 对同一范围的结果一致。
- AC2：spec-guard 项目里 `--module <id>` 按假设 4 推断范围：已完成的模块终点是最后一个已勾 gate 的提交，验收后的发版提交不算进来；
  进行中的模块标 `inProgress: true`；对 spec-guard 克隆的实测与人工核对一致（usage-draft 9 个提交、26 个文件 +995/−20；
  map-extra-columns 6 个提交）。
- AC3：`range.source` 与推断依据写明；混入别的模块文件的提交进 `warnings`。
- AC4：`module` 给出职责、依赖、Spec 批准标记、AC 列表、终点与 HEAD 两份 todo（含 gate／report 类型）；`usageDraft` 给出里程碑与入口。
- AC5：`links` 在公开 GitHub 且终点已推送时给提交 sha 的 blob 链接基址，否则给本机路径并写明原因；`--offline` 不发网络请求。
- AC6：`size` 给出文件数、增删行、字节数与估算 token 数。
- AC7：只读：跑完后被讲解项目的工作区与全部 ref 不变（测试守护）。
- AC8：参数错、模块不在能力图上、找不到提交、不是 git 仓库，各按假设 3 的退出码报一行中文说明，不抛堆栈。
- AC9：`claude plugin validate .` 通过（marketplace 与 plugin 清单）。

## 文档建议

- 本模块自己的：`docs/facts-schema.md` 写 JSON 字段表与范围推断规则（module-brief 和以后的 sg-coord 接口对接都要看）。
  README 只放一段「开发中」，完整说明等 M1 发版。

## 待定问题

- 无。
