# Plan: brief-facts

<!-- spec-guard: review approved -->

依据 [`spec/brief-facts.md`](../../spec/brief-facts.md)（2026-11-19 用户在本会话批准：「批准」，与能力图、用法草案
[`spec/usage/delivery-brief.md`](../../spec/usage/delivery-brief.md) 一起，提交 `e18eb95`）。
分支 `main`（本仓库还没有远端），串行，在本会话做。本模块不发版，版本号在 M1 发版时定。

## Overview

先搭插件骨架，再按「显式提交段 → spec-guard 文件解析 → 模块范围推断 → 链接判断」的顺序一层层加事实，每层先写失败的测试再实现。
最后用 spec-guard 仓库的临时克隆实跑两个真实模块，和人工核对的结果比对。

## Architecture Decisions

1. **布局照 delegate-plugin**：根 `.claude-plugin/marketplace.json`，插件 `plugins/delivery-brief/`。脚本放
   `plugins/delivery-brief/scripts/`：`brief_facts.py`（命令行与组装 JSON）、`facts_git.py`（调 git）、`facts_specguard.py`
   （解析能力图、Spec、todo、用法草案）、`facts_links.py`（链接基址）。四个文件各管一类事实，不再加更深的包结构。
2. **git 一律走子进程**：`git -c core.quotepath=off --no-pager`，路径相关输出用 `-z` 解析（重命名、空格、中文路径都不出错），
   每次调用设超时；不写任何 git 状态（不 fetch、不 checkout、不改 ref）。读历史版本的文件用 `git show <sha>:<path>`，不碰工作区。
3. **JSON 带 `schemaVersion: 1`**，字段名与 Spec 假设 5 一致；`docs/facts-schema.md` 是字段的唯一说明，module-brief 照它读。
4. **范围推断**按 Spec 假设 4：起点用 `git log --reverse --no-merges -- spec/<id>.md tasks/<id>/` 的第一个；终点逐个检查改过
   `tasks/<id>/todo.md` 的提交，比较前后两版里「`（gate）`」行的勾选，取最后一个让某个 gate 从未勾变已勾、且之后该 gate 仍是已勾的提交。
   推断依据（起点、终点各是哪个提交、哪一行 gate）原样写进 `range.basis`。
5. **网络只有 `gh`**：`gh api repos/<owner>/<repo>` 取可见性，`gh api repos/<owner>/<repo>/commits/<sha>` 判断终点是否在远端；
   每次 10 秒超时；`--offline`、没有 `gh`、或 `gh` 失败时退回本机链接并写原因。测试用 PATH 里的假 `gh` 脚本，不连网。
6. **测试**：`unittest`，夹具在临时目录现建 git 仓库（`tests/fixtures.py` 提供造仓库、造 spec-guard 文件、提交的帮手）。
   每个用例结束比对工作区与全部 ref，守住只读。系统自带 Python 3.9.6 与 Homebrew Python 各跑一次。

## Task List

### Task 0：提交 Plan 与 todo

- 验证：verify-artifacts 0 失败。

### Task 1：插件骨架

- 文件：`.claude-plugin/marketplace.json`、`plugins/delivery-brief/.claude-plugin/plugin.json`、`README.md`（一段「开发中」）、`.gitignore`。
- 验证：`claude plugin validate .` 通过（AC9）。

### Task 2：显式提交段的事实（AC1、AC6、AC7、AC8 的一部分）

- 文件：`scripts/brief_facts.py`、`scripts/facts_git.py`、`tests/fixtures.py`、`tests/test_range.py`。
- 用例：`--range a..b` 的提交与逐文件增删和 git 原生命令一致（含重命名、二进制、中文路径）；`size` 各字段；
  参数错退出 2、不是 git 仓库退出 4、范围解析不了退出 3，都只出一行中文、无堆栈；跑完工作区与 ref 不变。
- 验证：先红后绿。

### Task 3：spec-guard 文件解析（AC4）

- 文件：`scripts/facts_specguard.py`、`tests/test_specguard.py`。
- 用例：能力图行（职责、依赖）；Spec 批准标记与 AC 列表；todo 各项与类型（gate／report／普通，含延期写法）；
  用法草案里本模块的里程碑与入口；终点与 HEAD 两份 todo 不同时都给出；文件缺失或写坏时进 `warnings` 不中断。
- 验证：先红后绿。

### Task 4：模块范围推断（AC2、AC3、AC8 其余部分）

- 文件：`scripts/brief_facts.py`、`scripts/facts_git.py`、`tests/test_module_range.py`。
- 用例：完成的模块终点是最后一个已勾 gate 的提交，验收后的发版提交不算进来；进行中的模块 `inProgress: true`；
  范围内混入别的模块文件的提交进 `warnings`；有合并提交时只列非合并提交；模块不在能力图上退出 3；`range.source` 与 `range.basis` 写全。
- 变异：把终点改成「最后一次改 todo」，至少一个用例变红。
- 验证：先红后绿，变异变红。

### Task 5：链接基址（AC5）

- 文件：`scripts/facts_links.py`、`tests/test_links.py`。
- 用例：假 `gh` 报公开且提交在远端 → GitHub blob 基址（终点 sha）；私有、提交不在远端、`gh` 失败或缺失 → 本机路径并写原因，
  另报本机工作区与终点是否一致；`--offline` 时假 `gh` 一次都没被调用。
- 验证：先红后绿。

### Task 6：文档

- 文件：`docs/facts-schema.md`（字段表、退出码、范围推断规则与已知局限）。
- 验证：字段表与一次真实输出的键逐一对得上（测试里读文档的字段名比对，防漂移）。

### Checkpoint 1（report）：完整检查与实测

- 系统 `/usr/bin/python3`（3.9.6）与 Homebrew Python 各跑全部测试；`claude plugin validate .`。
- 实测：spec-guard 仓库临时克隆（远端 main `291a0c74`）跑 `--module usage-draft --offline` 与 `--module map-extra-columns --offline`，
  起止提交、提交数、文件数与增删和人工核对一致（usage-draft 9 个提交、26 个文件 +995/−20；map-extra-columns 6 个提交）；
  再不加 `--offline` 跑一次 usage-draft，看链接基址是否给出 GitHub。结果记进 todo。

### Checkpoint 2（gate）：最终验收

- 呈现：做了什么、AC1–AC9 的证据（测试断言与实跑输出）、改动表、提交表、偏离计划处、拟回告原文。
- 本仓库没有远端，这一步**不含推送、不开 PR**；通过后只勾 gate 并本地提交，接着写 module-brief 的 Spec。

## Files likely touched

- 新增：`.claude-plugin/marketplace.json`、`.gitignore`、`README.md`、`docs/facts-schema.md`、
  `plugins/delivery-brief/.claude-plugin/plugin.json`、`plugins/delivery-brief/scripts/{brief_facts,facts_git,facts_specguard,facts_links}.py`、
  `plugins/delivery-brief/tests/{fixtures,test_range,test_specguard,test_module_range,test_links}.py`。
- 记录：本 Plan、`tasks/brief-facts/todo.md`。
- 新增依赖、锁文件：无。不碰 spec-guard 仓库（实测只在 scratchpad 的临时克隆里只读运行）。不改全局配置。

## 风险

- **todo 写法不统一**：别的项目的 gate 行若不写「（gate）」，会落到「进行中」兜底。缓解：`range.basis` 写明依据，页头标「推断」；
  有显式 `--range` 可覆盖；sg-coord 若补接口就改用接口。
- **并行开发混入别的模块提交**：只能发现「改了别的模块的 spec／tasks 文件」的提交，改共用代码的混入提交发现不了。缓解：进 warnings 的规则写进文档的已知局限。
- **`gh` 慢或要登录**：10 秒超时，失败即退回本机链接，不让收集失败。
- **Python 3.9 兼容**：不用 3.10 以后的语法（`match`、`X | Y` 类型写法），系统 3.9.6 跑一遍兜底。

## 预先声明

- Public paths: 无
- Dependencies: 无
- Configs: 无
- Patches: 无

## 返工（0.1.1）

2026-11-19 用户在 cross-check 最终验收时同意先发 0.1.0、README 列已知问题、之后修；按 spec-guard「返工与小模块」规则，
这批是本模块已批准范围里的缺口（AC5、AC7、AC8 与 Task 3 用例「文件缺失或写坏时进 warnings」），在本模块内返工，不开新模块、不重新交审。
来源：`/delivery-brief:brief brief-facts --cross-check` 的 10 条 confirmed 发现里针对代码的 5 条。

### Task 7：非 UTF-8 路径不抛堆栈（AC8）

- 文件：`scripts/facts_git.py`、`scripts/brief_facts.py`、`tests/test_range.py`。
- 做法：git 输出里的路径按 UTF-8 解码失败时用替换字符显示，不中断；`warnings` 记一条「有 N 个路径不是 UTF-8」并列出前几个。
- 用例：用 `git update-index --cacheinfo` 造一个非 UTF-8 路径的提交（macOS 不让建这种文件名），`--range` 退出 0、warnings 有这一条、没有堆栈。

### Task 8：分开「终点不在远端」与「gh 查询失败」（AC5）

- 文件：`scripts/facts_links.py`、`tests/test_links.py`。
- 做法：`gh api …/commits/<sha>` 失败时看 stderr：带 `HTTP 404` 或 `HTTP 422` 才算不在远端；其他失败（网络、权限、限流、超时）写「gh 查询终点提交失败：原因」。
- 用例：假 gh 分别给 422 与 403，`links.reason` 不同。

### Task 9：读不到的文件进 warnings（Task 3 用例）

- 文件：`scripts/brief_facts.py`、`tests/test_module_range.py`。
- 做法：模块的 todo 在终点或 HEAD 读不到、用法草案读不到时各记一条 warning（没有 Plan 仍只记 `plan.exists: false`，没有 `spec/usage/` 不算问题）。

### Task 10：终点之后只改代码的提交（AC3 的提示）

- 文件：`scripts/brief_facts.py`、`docs/facts-schema.md`、`tests/test_module_range.py`。
- 做法：新增 `range.basis.laterCodeOnlyCommits`：终点之后、下一个改动别的模块 spec／tasks 文件的提交之前，没改任何 `spec/`、`tasks/` 文件的非合并提交；有则进 warnings。只增字段，不改终点。
- 用例：gate 之后补一个只改代码的提交 → 字段与 warning 都有；之后紧接别的模块的提交不算进来。

### Task 11：收紧只读与报错测试（AC7、AC8）

- 文件：`tests/fixtures.py`、`tests/test_range.py`。
- 做法：快照加上工作区每个文件的内容摘要（不只看 status）；非仓库目录也做快照；`assertOneLineError` 断言报错含中文。
- 验证：故意让收集脚本写一个文件（草稿副本里变异）时快照测试变红。

### Checkpoint 3（gate）：返工验收

- 两个 Python 版本全部测试；`claude plugin validate .`；对本仓库重跑 `--module brief-facts` 看 warnings。
- 呈现：每条已知问题的修法与证据、改动表；之后问发 0.1.1（推送、打标签各问一次）。
