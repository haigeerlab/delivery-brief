# Usage draft: delivery-brief

交付讲解：按需调出模块与里程碑讲解页（总账 S90）。

## Entry points

| Entry | Does | Module |
|---|---|---|
| `/delivery-brief:brief <模块 id>` | 在 spec-guard 项目里讲一个模块：推断提交范围，生成模块讲解页并给出本机路径 | module-brief |
| `/delivery-brief:brief <base>..<head>` | 讲任意一段提交（没装 spec-guard 也行） | module-brief |
| `brief_facts.py` | 只读收集事实并输出 JSON（命令内部调用，也可单独跑来核对范围） | brief-facts |
| `--cross-check` | 生成后派 delegate 只读核对事实，改正核实成立的问题 | cross-check |
| 截图（自动） | 有界面改动且能起开发服务器时，清单里的页面附截图；否则写明未生成 | ui-screenshots |
| `/delivery-brief:brief --milestone <M>` | 生成里程碑讲解页并链接各模块页 | milestone-brief |

## Typical usage

### U1: 模块交付后看讲解

一个模块刚通过最终验收（或事后想补看以前的模块），你输入 `/delivery-brief:brief usage-draft`。先看到这次要读多少 diff，
确认后得到 `~/.claude/delivery-brief/<项目>/usage-draft.html`：为什么改、产出清单、分层讲解、阅读路线、需要你判断的、附录。
页头写明提交范围从哪推断出来。想更放心时加 `--cross-check`：讲解先经另一个模型核对，页脚多一行核对摘要，附录里有逐条核对记录。

### U2: 前端模块带截图

讲一个改了页面的模块。命令按项目的启动方式起开发服务器，产出清单里的页面各附一张截图；服务起不来时页面照样生成，
写明「截图未生成」和原因。

### U3: 一个里程碑做完

用法草案里一个里程碑的模块都做完了，你输入 `/delivery-brief:brief --milestone M1`，得到里程碑讲解页：代码地图标出这一站新增和
改动的部分，沿这一站的典型用法走一遍完整链路，列出新出现的跨模块约定，每个模块链到它的模块讲解页。

## Milestones

| Milestone | Usage | Modules |
|---|---|---|
| M1 | U1 | brief-facts, module-brief, cross-check |
| M2 | U1, U2 | ui-screenshots |
| M3 | U1, U2, U3 | milestone-brief |
