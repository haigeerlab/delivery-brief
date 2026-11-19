# Spec: milestone-brief

<!-- spec-guard: review approved 413f0d29a2ef -->

## 目标

`/delivery-brief:brief --milestone <M>`：一个里程碑的模块都做完后，生成一份**里程碑讲解页**，让人几分钟看懂这一站整体做成了什么：
代码地图标出这一站新增和改动的部分，沿这一站的典型用法走一遍完整链路，列出新出现的跨模块约定，每个模块链到它的模块讲解页。

对外接口与用法草案 `spec/usage/delivery-brief.md` 一致：入口表 `/delivery-brief:brief --milestone <M>` 一行（M3），U3「得到里程碑讲解页：
代码地图标出这一站新增和改动的部分，沿这一站的典型用法走一遍完整链路，列出新出现的跨模块约定，每个模块链接到它的模块讲解页」。
与草案的差异：多一个可选参数 `--draft <路径>`，项目有多份用法草案时用来指定读哪一份（草案没写，属于补充）。

给谁用：一个里程碑做完、想从整体上看这一站的人；和模块页互补——模块页讲一个模块的细节，里程碑页讲模块之间怎么串起来。

本模块是能力图的最后一个模块，完成即 M3，版本 0.3.0。

## 假设

1. **里程碑从用法草案读**：`brief_facts.py --milestone <M> [--draft <路径>]` 读 HEAD 上 `spec/usage/*.md` 的 Milestones 表，取出这一行的
   典型用法与模块；只有一份草案时不用 `--draft`；有多份且没给时退出 2 并列出草案；找不到草案或里程碑退出 3。
2. **范围是各模块范围的并集**：对每个模块沿用模块范围推断（起点、终点、进行中），里程碑范围的起点取最早那个模块起点的父提交，
   终点取最晚那个模块的终点（按提交先后，不按时间戳）。范围里的提交、文件、增删由脚本照常生成；模块没做完、里程碑还没确认的写进 `warnings`，页头标「进行中」。
3. **新增 facts 字段 `milestone`**（只在 `--milestone` 时有）：`id`、`draft`、`usages`（编号与标题）、`confirmed`（草案里有没有确认行）、
   `modules[]`（每个模块的 `id`、职责、`range`、`status`）。另加 `codeMap`：终点提交上的目录树，按第一、二层目录汇总，每个目录给
   新增、修改、未改的文件数，由脚本生成，不经模型。
4. **页面固定七节**（检查脚本按里程碑页的规则检查，和模块页的六节分开）：
   1. 这一站做成了什么：逐条对照草案里这一站的典型用法，每条给证据（代码、测试或实跑输出的引用）；
   2. 代码地图：渲染脚本从 `codeMap` 画（目录树，新增／修改／未改着色），agent 只在下面写几句怎么读；
   3. 沿典型用法走一遍：选一个典型用法，按顺序 3～10 步，每一步引用代码、标出属于哪个模块；
   4. 跨模块约定：这一站新出现的、多个模块都遵守的约定（文件格式、字段、退出码、命名），每条至少引用两个模块里的代码；没有就写「没有新约定」；
   5. 各模块讲解：渲染脚本按 `milestone.modules` 生成表格：模块、职责、范围、讲解页链接；
   6. 需要你判断的：同模块页的规则，每条带证据；
   7. 附录：文件表与提交表，同模块页。
5. **模块页链接**：模块页在同一个输出目录（`<模块 id>.html`）时用相对路径链接；不存在时表格里写「还没生成」并给出生成命令，见待定问题 Q1。
6. **读取策略**：里程碑范围往往很大（本仓库 M1 是 38 个文件、diff 约 24 万字节，会触发规模停点），按「先读各模块的 Spec 成功标准和模块页（有的话）、再读跨模块的接口处」的顺序读，
   不整读全部 diff；规模停点沿用 `size.diffBytes` 超过 200000 时先问。
7. **复用现有部件**：引用语法、检查、渲染、实跑在导出目录里跑、`--no-open`、输出目录都沿用模块页；输出文件名 `milestone-<M>.html`。
   截图不做（截图属于模块页）；`--cross-check` 见待定问题 Q2。
8. **M3 发版**：README 加里程碑页说明；版本 0.3.0；本机升级、推送、打标签各自先问；发版后回告 ecosystem-lead。

## 命令

```text
python3 -B -m unittest discover -s plugins/delivery-brief/tests
python3 -B plugins/delivery-brief/scripts/brief_facts.py --project . --milestone M1
python3 -B plugins/delivery-brief/scripts/check_brief.py --facts <facts.json> --source <milestone.md>
python3 -B plugins/delivery-brief/scripts/render_brief.py --facts <facts.json> --source <milestone.md> --out <milestone-M1.html>
/delivery-brief:brief --milestone M1 --project ~/Documents/haigeerlab/delivery-brief
claude plugin validate .
```

## 项目结构

```text
plugins/delivery-brief/scripts/brief_facts.py        # --milestone、--draft；milestone 与 codeMap 字段
plugins/delivery-brief/scripts/facts_specguard.py    # 读里程碑表的一行、确认行
plugins/delivery-brief/scripts/check_brief.py        # 按 facts 里有没有 milestone 选模块页或里程碑页的规则
plugins/delivery-brief/scripts/render_brief.py       # 代码地图、各模块讲解表
plugins/delivery-brief/commands/brief.md             # --milestone 的流程
plugins/delivery-brief/references/brief-rules.md     # 里程碑页七节各写什么
docs/facts-schema.md                                 # 新字段
plugins/delivery-brief/tests/                        # 范围并集、codeMap、检查、渲染
```

## 测试策略

- 事实：夹具仓库里两个模块都做完、同属一个里程碑，`--milestone` 的范围是两个模块范围的并集；一个模块进行中时进 warnings 且标进行中；
  里程碑确认行读得出；多份草案没给 `--draft` 退出 2；草案或里程碑不存在退出 3；`codeMap` 的新增、修改、未改文件数与 git 对得上；被讲解项目不变。
- 字段文档：新字段写进 `docs/facts-schema.md`，文档测试比对。
- 检查：里程碑页缺节、顺序错、对照用法没有证据、走一遍的步数不在 3～10、约定少于两处引用，都报错；模块页的规则不受影响。
- 渲染：代码地图着色与数字来自 facts；各模块讲解表的链接（存在用相对路径、不存在写生成命令）；模块页的渲染结果不变（除生成时间）。
- 真实运行：对本仓库的 M1（三个模块）生成里程碑页，记录读了什么、检查几次、浏览器自验；再在新会话里用安装后的版本端到端跑一次。

## 边界

- Always：数字与代码地图由脚本生成；对照用法、走一遍、约定都带引用证据；不写被讲解项目；模块没做完照实标出。
- Ask first：本机升级插件、推送、打标签；要替缺的模块页逐个生成时（见 Q1 的 B）。
- Never：给里程碑或模块打分；把没做完的模块说成做完；改 spec-guard 或被讲解项目的文件。

## 成功标准

- AC1：`brief_facts.py --milestone <M>` 按假设 1、2、3 给出范围、`milestone`、`codeMap`，各种错误按退出码报一行中文；被讲解项目不变。
- AC2：`docs/facts-schema.md` 写全新字段，文档测试守护。
- AC3：`check_brief.py` 对里程碑页按假设 4 的七节规则检查；模块页的检查结果不变。
- AC4：`render_brief.py` 渲染代码地图与各模块讲解表，链接按假设 5；模块页渲染结果不变（除生成时间）。
- AC5：命令文件与讲解规则写明 `--milestone` 的流程、读取策略、七节写法；新参数都在脚本 `--help` 里（测试守护）。
- AC6：对本仓库 M1 真实生成一次里程碑页，检查通过、浏览器自验，结果写进验收材料。
- AC7：M3 发版准备：README、版本 0.3.0、`claude plugin validate .`；本机升级后在新会话端到端跑一次；推送、打标签、本机升级各自先问。

## 文档建议

- README「用法」加 `--milestone <M>` 与 `--draft`，「后续计划」一节在能力图完成后改为当前状态；最终验收时按能力图全部完成再提一次收尾文档建议。

## 待定问题

- 无。2026-11-19 用户定为「批准；Q1 A；Q2 A」：缺的模块页只标出「还没生成」和生成命令，不替你生成（假设 5）；
  里程碑页这一版不支持 `--cross-check`，给了就说明并照常生成（假设 7）。
