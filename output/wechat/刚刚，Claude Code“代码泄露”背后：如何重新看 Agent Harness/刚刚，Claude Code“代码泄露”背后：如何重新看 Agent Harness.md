# 刚刚，Claude Code“代码泄露”背后：如何重新看 Agent Harness

> 公众号: 架构师
> 发布时间: 2026-03-31 22:13
> 原文链接: https://mp.weixin.qq.com/s/LjJTvP2fCWEMWNYChNm7Og

---




架构师（JiaGouX）我们都是架构师！
架构未来，你来不来？

---

这两天 AI Coding 圈里最热的话题之一，是 Claude Code 的“源码泄露”。

但把这件事只写成“源码泄露”，还是有点粗。

更准确一点说，是 Anthropic 分发出去的 npm 包里带出了 `cli.js.map`。而这份 source map 又恰好给了外界一个很少见的观察窗口，让人能从打包产物一路映射回接近开发态的模块结构、源码路径和不少实现细节。

于是，讨论很快从“到底漏了多少代码”转向了另一件更有意思的事：

**Claude Code 这套 agent harness，到底已经长成什么样了。**

前两天我们在《[大家都在讲 Harness，但它到底该怎么理解](https://mp.weixin.qq.com/s?__biz=MzAwNjQwNzU2NQ==&mid=2650408900&idx=1&sn=93bbae7c90fc03fb510f450c6fee97e0&scene=21#wechat_redirect)》里刚把 Harness 的三层结构拆开聊过，今天就多了一份可以对照着看的真实样本。

如果结合泄露的代码去看，能看到的就不只是几个彩蛋目录，而是一套已经很完整的运行时：

- • 有主循环
- • 有工具池和权限上下文
- • 有任务运行时
- • 有长期记忆整理
- • 还有跨本地与远程的权限桥接

从架构和工程的角度看，这比“源码泄露”四个字本身更值得写。

因为一旦一个 AI 不只是会说，而是真的会读文件、跑命令、调工具、发起远程任务，外界迟早会追问一件事：

**它的安全边界，究竟停留在产品文案里，还是已经被做成了工程现实。**

![Image](images/img_001.png)行业传播截图

有意思的是，Claude Code 自己读到这份代码后，给出了“这就是我的代码库”的判断。

它当然不能单独当证据，但很能解释为什么行业注意力会这么快从“能不能看到代码”，转到“这套 harness 到底长什么样”。

---

## 先看看边界

这件事里需要先分清楚的，是到底暴露了什么、没暴露什么。

更准确一点说，这次公开可见的内容，主要集中在：

- • npm 分发物里的 `source map`
- • 由此还原出的客户端实现细节
- • 工具调用、权限模式、任务状态、上下文和记忆相关的代码结构

它不等于模型权重泄露。

也不等于 Anthropic 后端被攻破。

更不等于“发现了一个任何人都能直接利用的后门”。

如果起手就用“完整闭源系统被扒光”这种说法，后面的讨论很容易偏。

但如果只把它理解成“打包失误”，也还是轻了。

原因不在于 source map 本身有多戏剧性，而在于 Claude Code 这类产品，已经不再是一个纯文本回答器。

它是会动手的。

模型只回答错，通常还是认知问题。但一旦开始动手，问题就变成了系统动作：

- • 文件会不会被改错
- • 命令会不会跑错
- • 工具会不会被误用
- • 权限会不会漂移
- • 后台任务会不会在你不注意的时候继续推进

所以今天这件事真正值得写的，不是“有没有泄露”，而是：

**我们借着这次风波，看到了一个 AI Agent 产品的 shipped implementation，到底已经长成什么样了。**

---

## 它是怎么漏出来的，大家又是怎么拿到的

这次的链路并不复杂。

按照目前社区里流传最广的说法，问题出在 `@anthropic-ai/claude-code@2.1.88` 的 npm 分发包里带出了 `cli.js.map`，一个 57MB 的文件，里面包含 4756 个源文件的完整路径与内容。

其中约 1906 个是 Claude Code 自身的 TypeScript/TSX 源码，剩下 2850 个是 node\_modules 依赖。

source map 本来是为了把打包后的产物映射回原始源码，方便调试。它本身只是一份 JSON，里面有两个关键数组，`sources`（文件路径）和 `sourcesContent`（对应的完整源码），两者索引一一对应。所以一旦 map 文件被分发，外界不需要反编译，不需要反混淆，`sourcesContent` 里存的就是一字不差的原始代码。

更直接的获取方式，其实也不需要什么高门槛操作。

社区里常见的做法就是两步：

- • 拉取对应版本的 npm 包
- • 解包后直接查看 `cli.js.map`

网上还流传着一组复现命令：

```
npm pack @anthropic-ai/claude-code@2.1.88 --registry=https://registry.npmjs.org/
npm install
npm run build
node dist/cli.js --help
```

不过从工程角度说，真正关键的并不是这组命令最后能不能把 CLI 跑起来，而是 `.map` 文件本身已经把不少打包逻辑重新指回了 `src/query.ts`、`src/tools.ts`、`src/Tool.ts`、`src/services/autoDream/autoDream.ts` 这一类更接近开发态的实现位置。

也正因为如此，这次外界拿到的重点，不是“某个压缩后的 JS 很难读”，而是“很多实现细节突然变得足够可读”。

如果把这条链路画开，主线会更清楚：

![Image](images/img_002.png)

## 行业内最热的，不止一种讨论

这两天行业里的讨论，大致可以分成三类。

第一类在数“到底漏了多少”。

社区把还原出的代码打包归档上传到了 GitHub，短短几小时 Star 数就破万。大家盯着 `sources`、`sourcesContent`，数出约 1900 个文件、超 51.2 万行 TypeScript 代码，规模接近一个中型 App 的完整代码量。这类讨论的重点，是这份 map 到底把可见性拉高到了什么程度。

第二类在做纠偏。

这类声音通常会提醒一句：别把它写成“完整源码开源”或者“后端被扒光”。有开发者直接指出：Claude Code CLI 的代码在 npm 包里一直是可读的（minified JS），source map 只是让它变成了可读的 TypeScript；Anthropic 从来没把 Claude Code 的客户端逻辑当秘密，核心壁垒是 Claude 模型本身，不是 CLI 工具。更准确的说法，是 shipped implementation 因为 source map 变得更容易被细粒度分析了。

第三类最容易写飘，但也最有意思。

顺着 `KAIROS`、`COORDINATOR_MODE`、`AGENT_TRIGGERS`、`ULTRAPLAN`、`autoDream` 这些 feature gate 往下看，很多人开始讨论 Claude Code 接下来会不会从 CLI 助手继续往持续助手、多代理调度、远程工作流、团队记忆这些方向走。有人甚至把 KAIROS（持续在线助手）+ Coordinator（多 agent 编排）+ ULTRAPLAN（远程规划）+ Auto-Dream（记忆整合）串起来，说"这就是一个能思考、计划、执行、学习、做梦的系统"。

这个角度确实有参考价值。但更稳妥的写法，应该把它当成"路线信号"而不是"已公开功能表"，这些 feature gate 说明系统里存在对应能力或实验入口，但不能直接写成"官方即将发布"。

这条线其实和我们前面写的是同一根。在《Codex 为什么能又快又稳：他们把工程经验写进了仓库》里，我们看到 OpenAI 怎么把经验沉淀进仓库结构。Claude Code 这次的风波，等于让我们看到了 Anthropic 那边对应的工程现实。

---

## 这也不是 Anthropic 这周第一次因为信息暴露被讨论

如果把时间线稍微拉长一点，这已经不是 Anthropic 这周第一次因为本不该公开的信息进入舆论中心。

3 月 26 日到 3 月 29 日之间，外界已经在讨论另一起 CMS 配置错误导致的未发布材料暴露。按照 Fortune 的首先报道，以及 Axios 在 2026 年 3 月 29 日的跟进，那次暴露让外界提前看到了约 3000 份内部文件，其中包含还没发布的新模型 Claude Mythos 相关草稿和内部表述。Anthropic 回应说那次是"人为操作失误"。

这和今天的 Claude Code/source map 风波不是同一种问题。

前者更像内容发布链路暴露，后者更像分发物把调试映射一并带了出去。两次都是人为失误，两次都不涉及用户数据或模型核心。

但五天之内连着发生，会明显放大外界对 Anthropic 分发链路、发布链路和安全边界的敏感度。

---

## 它真正暴露出来的，更像一套 harness

如果把 `claude-code` 这个 GitHub 仓库按架构与工程的视角拆开看，你会发现，最有价值的不是某个彩蛋，也不是某个隐藏开关。

最有价值的是：它已经非常明显地不是“聊天 + 工具调用”这么简单。

从技术栈看，Claude Code 用 React + Ink 构建 CLI 界面，运行于 Bun 运行时，核心是一个 REPL 循环，支持自然语言输入和 slash 命令，底层通过工具系统与 LLM API 交互。约 40 个工具模块、50 个斜杠命令、140 个界面组件。

它内部至少已经形成了五层比较清楚的结构：

![Image](images/img_003.png)

下面让我们逐层看。

---

## 第一层：主循环不是对话，而是 agentic turn orchestration

在《[如何让单个 Agent 做长任务不失真](https://mp.weixin.qq.com/s?__biz=MzAwNjQwNzU2NQ==&mid=2650408877&idx=1&sn=d27eb9e99ed526e342df775f0291cb2e&scene=21#wechat_redirect)》里，我们拆过 Anthropic 在 Harness 设计上对运行时的思考。这次从 `src/query.ts` 里，能更直接地看到它在产品里到底长什么样。

这个文件里不是单次 API 调用的轻量封装，而是一套带状态的查询循环。

里面同时挂着几类东西：

- • `runTools`
- • `StreamingToolExecutor`
- • `tokenBudget`
- • `handleStopHooks`
- • `autoCompact`
- • `reactiveCompact`
- • `toolUseSummary`

这意味着 Claude Code 的主循环，并不是“用户提问，模型回答”。

它更像下面这种东西：

![Image](images/img_004.png)

这里最关键的，不是它会不会调工具。

而是它已经把下面这些“运行时问题”正式建模了：

- • token budget 怎么算
- • 什么时候 compact
- • API 失败后怎么恢复
- • 工具执行结果怎么回写
- • 本轮 agentic turn 何时继续，何时停

一旦系统长成这样，你就不能再把它看成“一个更强的终端助手”了。

它更像一个小型执行运行时。

这也是为什么今天 source map 风波会让工程师兴奋。

因为大家看到的，不只是 UI 或 prompt，而是这套主循环怎么把“思考、行动、恢复、压缩、继续”串起来。

---

## 第二层：工具系统已经不是能力列表，而是控制面的一部分

如果只看 `src/tools.ts` 的文件名，会以为这只是工具注册表。

但把它和 `src/Tool.ts` 一起看，味道就完全不一样了。

这里能看到几个非常重要的信号。

### 1. 工具池是分层装配的

它不是把所有工具一股脑暴露给模型，而是按条件组装：

- • built-in tools
- • feature-gated tools
- • MCP tools
- • REPL mode 下的特定可见性
- • coordinator mode 下的特定组合

像 `KAIROS`、`AGENT_TRIGGERS`、`MONITOR_TOOL`、`WORKFLOW_SCRIPTS` 这些能力，都不是“写死在系统里”，而是通过 feature gate 控制是否进入工具池。

![Image](images/img_005.png)

这说明 Claude Code 的演进方式，很像一个持续增长的 agent platform，而不是一次性固定能力集。

### 2. 权限过滤发生在模型看到工具之前

`filterToolsByDenyRules` 的处理方式不是“让模型先看到，再在调用时拦”，而是在工具池装配阶段就先剔除。

这意味着：

**权限系统并不是事后纠错，而是前置塑形。**

模型能看到什么、不能看到什么，本身就是控制面的一部分。

### 3. 权限不是布尔值，而是状态机

`ToolPermissionContext` 里最值得注意的，不是 `allow` 或 `deny`，而是它其实已经建了一整套状态：

- • `alwaysAllowRules`
- • `alwaysDenyRules`
- • `alwaysAskRules`
- • `isBypassPermissionsModeAvailable`
- • `isAutoModeAvailable`
- • `prePlanMode`
- • `shouldAvoidPermissionPrompts`
- • `awaitAutomatedChecksBeforeDialog`

这已经不是简单的“是否需要确认”了。

它更像一个跨模式、跨角色、跨会话的权限状态机。

值得一提的是，Anthropic 自己在 3 月 25 日的工程博客里直说：用户面对大量确认框会产生"approval fatigue"，实际中用户会接受 93% 的权限提示。他们因此推出了 Auto mode，试图在"完全手动确认"和"完全跳过权限"之间找折中。

更关键的是，那篇官方文章还举了内部 incident log 的例子：包括误删远程 Git 分支、把工程师的 GitHub auth token 上传到内部计算集群、尝试对生产数据库做迁移。

所以今天很多人盯着 `bypassPermissions` 或 Auto mode 这些词看，其实抓到的不是八卦点，而是真问题。

真正的问题是：

**当一个 Agent 进入 plan mode、background mode、remote mode、coordinator mode 时，权限上下文是怎么继承、怎么切换、怎么回退的。**

一个系统最危险的时候，往往不是“完全没权限”，而是“权限自己漂了”。

---

## 第三层：它已经开始像任务运行时，而不是单会话 CLI

再往下看 `Task.ts` 和 `tasks/` 目录，会更明显。

Claude Code 内部不是只存在一种“会话”。

它把执行单元明确拆成了多种任务类型：

- • `local_bash`
- • `local_agent`
- • `remote_agent`
- • `in_process_teammate`
- • `local_workflow`
- • `monitor_mcp`
- • `dream`

这组类型非常说明问题。

因为它意味着系统已经把这些场景正式纳入运行时模型：

- • 本地动作
- • 本地子代理
- • 远程代理
- • 进程内 teammate
- • 工作流
- • 持续监控
- • 记忆整理

这和传统“命令行工具”的想法差别非常大。

![Image](images/img_006.png)

### 主会话可以 background

`LocalMainSessionTask` 里直接写得很清楚：

- • 用户在查询过程中按两次 `Ctrl+B`
- • 当前会话进入 background
- • 查询继续在后台跑
- • UI 回到新的 prompt
- • 任务完成后再通知

这不是一个普通 CLI 的行为。

这是非常典型的任务运行时思路：

**前台交互和后台执行被拆开了。**

更细一点看，它连 transcript 都不是复用主会话文件，而是专门给 background task 单独建输出路径，避免 `/clear` 之后把主会话污染掉。

这个细节不大，但和长任务跑起来之后的稳定性直接相关。

### 进程内 teammate 不是玩具，而是正式任务类型

`InProcessTeammateTask` 也很有代表性。

它明确写了几件事：

- • teammate 在同一 Node.js 进程内运行
- • 用 AsyncLocalStorage 做隔离
- • 有 team-aware identity
- • 支持 plan mode approval flow
- • 可以 idle，也可以 active

这意味着 Claude Code 对“多代理”这件事的理解，不是简单地再起几个线程。

它已经开始认真处理：

- • 身份
- • 生命周期
- • 状态切换
- • 消息注入
- • 任务选择与展示顺序

换句话说，这不是 demo 级“我也支持多 agent”。

这是在把多代理当成正式产品能力做。

---

## 第四层：记忆层已经是工程组件，不是聊天附属品

今天很多文档里都提到 `memdir`、`cost-tracker`、`buddy` 这些东西。

最值得展开写的，是 `memdir` 和 `autoDream`。

因为它们比彩蛋更能说明 Claude Code 的野心。

### MEMORY 不是随便堆，而是有预算、有边界

`src/memdir/memdir.ts` 有几个设计很值得注意：

- • `MEMORY.md` 有明确的行数上限和字节上限
- • 超限时不是悄悄裁掉，而是补 warning
- • memory dir 会被 harness 主动创建
- • 系统明确告诉模型：目录已经存在，不要再浪费回合 `mkdir` 或探测

这些看起来像小事，但和我们在《别把 Skill 写成提示词》里聊过的问题是一回事：怎么减少模型的无效探路动作，把回合预算留给真正重要的事。

同时，代码里对记忆内容也不是无限开放的，而是倾向于 typed memory:

- • user
- • feedback
- • project
- • reference

而且明确排除了那些可以直接从当前项目状态推导出来的内容。

也就是说：

记忆不是第二份代码库索引，也不是第二份 README。

真正有价值的记忆，是项目状态推不出来、但跨会话又真的有用的那部分信息。

### Auto Dream : AI开始学会“做梦”?但本质还是记忆整理

再看 `src/services/autoDream/autoDream.ts`，就更清楚了。

如果借一点拟人化的说法，`/dream` 有点像系统在后台做一次“睡后整理”。

它会把最近积累下来的会话和记忆重新归拢一下。

但从工程角度说，更稳妥的表述还是：这是一套后台记忆整理机制，而不是某种已经完整成形的“做梦能力”。

它有一套非常克制的 gating 逻辑：

1. 1. 时间门槛
2. 2. 会话数量门槛
3. 3. 锁

顺序还专门按“最便宜优先”来排。

也就是说，系统不是想到就触发 `/dream`，而是在问：

- • 距离上次 consolidation 够久了吗
- • 最近真的积累了足够多会话吗
- • 有没有别的进程正在做同样的事

![Image](images/img_007.png)

更关键的是，它不是在主会话里做这件事，而是 fork 一个 subagent 到后台跑。

所以从代码里目前更稳妥能确认的，不是“Claude Code 已经把做梦这件事完整产品化了”，而是：

**它已经把长期记忆整理当成后台系统能力在设计。**

这说明 Claude Code 已经在认真处理一个未来几乎所有 agent 都绕不过去的问题：

**长期记忆如何在不打断主循环、不反复重入、不炸上下文的前提下，慢慢沉淀成系统能力。**

这不是“记不记得住你”的小彩蛋。

这是长周期 Agent 的核心工程题。

---

## 还有两个容易被放大的点：Undercover Mode 和 Buddy System

除了前面几层架构细节，这次源码里还有两个特别容易在社区传播中被放大的点。

**Undercover Mode** 确实存在。从代码里看，它是一个 `ant-only`（Anthropic 内部）的安全分支：当内部员工在公共或开源仓库操作时，会自动开启，避免泄露内部模型代号、未公开版本号和内部工具信息，甚至会主动剥离 `Generated with Claude Code` 和 `Co-Authored-By` 这类 AI 痕迹。它的默认策略是 `auto`，且没有 force-off。这在公关层面当然有争议，不过从工程上看，它更直接地说明 Anthropic 对模型输出表面和身份痕迹做了系统级的控制。

**Buddy System** 也不是空壳。它是一套已经接到交互层的电子宠物系统：18 种物种、5 种稀有度（普通 60% / 不常见 25% / 稀有 10% / 史诗 4% / 传奇 1%）、1% 闪光概率、5 项属性（调试力、耐心、混沌、智慧、嘴炮）。用用户 ID + 固定 salt + Mulberry32 伪随机数生成器确定性生成，同一用户永远看到同一只宠物。它不是 Claude Code 的主能力，但说明 Anthropic 也在认真经营使用习惯和长期留存。

这两个点合起来，一个偏控制，一个偏留存；一个偏外部输出治理，一个偏内部产品关系设计。它们都不在主能力中心，但能看出 Anthropic 在产品层面想得比较远。

---

## 第五层：远程权限桥接，让这件事多了一层现实感

如果前面几层还可以理解成“功能很全”，那 `remotePermissionBridge` 更值得关注的，是另一件事：

**权限不再是本地单点事件，而是一条跨环境链路。**

这个文件里做的事很朴素，但意义很大：

- • 远程环境里的 permission request，需要在本地 UI 上被确认
- • 因为远程容器里没有本地那条消息对象，所以系统会合成 synthetic assistant message
- • 如果远程工具本地没加载，还会先造一个最小 tool stub 来承接权限流程

![Image](images/img_008.png)

这说明什么？

说明 Claude Code 不是只在“本地 shell + 本地文件系统”这个简单边界里工作了。

它已经要处理：

- • 本地会话
- • 远程执行环境
- • 远程工具
- • 本地确认界面
- • 不同工具池的能力差异

也就是说，今天大家讨论的“权限模式”一旦放到真实工程里，问题很难被简化成一个弹窗。

真正的问题是：

**这条权限链路在跨端、跨工具、跨执行环境时，是否还能保持一致。**

所以更值得关注的，也不是有没有某个词条，而是这些安全边界到底有没有被做成真正生效的系统能力。

---

## 顺便回答一个很多人关心的问题：换 IP、换卡、换浏览器，有用吗

这次源码里还有一个细节，不属于 harness 架构，但可能是大家更加最关心的。

很多人被封号后，第一反应是换 IP、换虚拟信用卡、换家宽、换浏览器。

但从这次暴露出来的代码看，这些手段大概率白搭。

因为 Claude Code 默认收集的风控数据，远不止 IP 和浏览器指纹。

它至少包括：

- • **持久设备标识**：跨会话追踪同一物理设备，不是靠 cookie，而是更底层的设备 ID
- • **账户关联**：邮箱、账户 UUID、组织 UUID
- • **环境指纹**：完整的操作系统、硬件配置、软件环境参数、系统时区
- • **内容指纹**：从用户消息中提取字符生成的行为特征
- • **代码库关联**：Git 仓库远程 URL 的哈希值
- • **性能特征**：实时进程的资源占用情况

![Image](images/img_009.png)

Anthropic 的风控逻辑，不是在看"你从哪来"，而是在看"你是谁"。

设备 ID + 账户 UUID + Git 仓库哈希 + 消息内容特征，这几层叠在一起，传统的换 IP、换卡、换浏览器的做法，基本上只是换了一层皮。

来自@CuiMao

如果你比较在意这部分，账号侧能自己控制的默认开关，也值得顺手检查一遍。

![Image](images/img_010.png)

图片来自@ohmuyi

这也从另一个侧面印证了前面的观察：Claude Code 的系统能力，包括风控，已经远比"一个命令行工具"要深。

---

## 这件事为什么值得整个行业认真看一眼

如果把今天这场风波只当成一次“分发失误”，当然也说得过去。

但它确实把几个平时藏在产品包装后面的工程问题，一下子推到了台前。

### 1. 安全边界到底写在 prompt 里，还是写在系统里

一个系统如果只是说“危险模式请谨慎使用”，那它更像提醒。

但提醒不是边界。

真正的边界应该体现在：

- • 工具池能否前置裁剪
- • 高风险动作能否硬拦截
- • 后台任务能否避免弹不出确认框时继续误跑
- • 远程动作能否被本地权限层正确映射

### 2. 任务一旦长起来，权限就天然会复杂化

单回合小任务时，权限看上去很简单。

但 Claude Code 现在明显已经不是单回合系统了。

它有：

- • background session
- • remote agent
- • in-process teammate
- • dream task
- • workflow

一旦进入这些模式，权限和状态就一定会复杂化。

所以今天大家看到的，不是 Anthropic 独有的问题，而是所有做 Agent 的团队迟早都会面对的问题：

**权限不是按钮，是状态机；状态机不是配置项，是系统设计。**

### 3. 记忆、缓存、工具池这些“基础设施细节”，最后都会变成产品问题

过去做聊天产品，很多底层细节对用户几乎不可见。

现在做 Agent 不一样。

上下文压缩、Prompt caching、记忆写入、工具池大小、后台任务调度，这些东西最后都会直接影响：

- • 稳定性
- • 成本
- • 权限表现
- • 用户对“这个 Agent 靠不靠谱”的感知

从《[别把 Prompt Cache 只当优化技巧](https://mp.weixin.qq.com/s?__biz=MzAwNjQwNzU2NQ==&mid=2650408819&idx=1&sn=f0c65045a197c9a3a6ca5b19faeae4da&scene=21#wechat_redirect)》到《[模型越来越强，为什么大家却开始重写 Harness](https://mp.weixin.qq.com/s?__biz=MzAwNjQwNzU2NQ==&mid=2650408891&idx=1&sn=639dc4a7c8482f6e1ac04d8d53c63459&scene=21#wechat_redirect)》，我们一直在聊的就是这件事：这些底层工程细节，越来越不像纯实现，越来越像产品本身。

---

## 对做 Agent 的团队，这件事可能是一面镜子

如果把今天 Claude Code 这件事往后看一步，我觉得最值得带走的，不是“以后别把 source map 发出去”这种常识。

更值得带走的，是四个更现实的观察。

### 第一，客户端策略最好别被当成最终边界

客户端可以做很多事：

- • 提示
- • 分类
- • 约束
- • 过滤

真正高风险的能力，如果只靠客户端来守，通常还是会让人不太放心。

### 第二，经验如果全塞进 Prompt，往往走不远

这次仓库里最有价值的地方，恰恰不是 prompt 文本，而是：

- • tool pool
- • task runtime
- • permission context
- • memory pipeline
- • remote bridge

这更像一个成熟信号：当 harness 开始稳定下来，核心经验往往会从 prompt 慢慢外溢到系统层。

### 第三，长任务和多代理能力，最好配套隔离与恢复设计

background session、teammate、remote agent 这些能力很强，但如果没有：

- • 清楚的状态模型
- • 独立 transcript
- • 生命周期管理
- • 明确的通知与回收

系统很容易变得难以预测。

### 第四，安全讨论最终还是会回到工程细节

今天这场风波里，最值得记住的其实是：

未来大家评估 AI Agent，不会只看 demo，也不会只看模型榜单。

越来越多人会去看：

- • 你的任务循环怎么跑
- • 你的工具池怎么装
- • 你的权限状态机怎么切
- • 你的记忆如何限流与治理
- • 你的远程执行和本地确认怎么桥接

到那时，安全就不再是发布会上的一句话，而是仓库里每一层结构共同给出的答案。

---

## 最后想说的

今天这场风波的热闹会过去，但它留下的东西不会。

因为我们确实提前看到了一点未来。

未来的 AI Agent 产品，大概率会越来越像会动手的系统。

而一旦它们开始真正动手，外界也会越来越倾向于用软件工程最朴素的那套标准去看它们：

- • 你的边界清不清楚
- • 你的状态稳不稳定
- • 你的约束是不是真的生效
- • 你的恢复路径是不是想过

Claude Code 这次刚好站在了聚光灯下。

但它照出来的问题，是所有做 Agent 的人都在面对的：

**我们到底有没有把 Agent 的工程边界做成现实。**

---

如喜欢本文，请点击右上角，把文章分享到朋友圈如有想了解学习的技术点，请留言给若飞安排分享

**因公众号更改推送规则，请点“在看”并加“星标”第一时间获取精彩技术分享**

**·END·**

```
```
相关阅读：


- 模型越来越强，为什么大家却开始重写 Harness


- 如何让单个 Agent 做长任务不失真：Anthropic 给出了一套更工程化的答案
- Claude Code高手的 8 个 Claude Code 实战习惯
- 别从 README 开始：一个架构师会怎样翻 Codex 仓库
- Spec 不是代码的替代品，它是 AI Coding 的上下文管理层
- 如何让 Agents 自己设计、升级 Agents
- OpenAI怎么把开源项目维护做成工作流：Skills、AGENTS.md 和 CI 的一套组合拳
- Claude Skills 入门：把“会用 AI”变成“可复制的工程能力”
- 一套可复制的 Claude Code 配置方案：CLAUDE.md、Rules、Commands、Hooks
- Claude Code 最佳实践：把上下文变成生产力（团队可落地版）
- 把 AI 当成新同事：Agent Coding 的上下文与验证体系
- 一周写百万行的背后：Cursor长时间运行 Agent 的工程方法论
- 2026年生活重启指南
- 我真不敢相信，AI 先加速的是工程师。
- 扒一扒 Claude Cowork 系统提示词：Anthropic 如何打造数字同事
- Cowork 安全架构深度解析：从 Claude Code 到 Cowork，Anthropic 如何把“可控”做成产品
- Anthropic官方万字长文：AI Agent评估的系统化方法论
- 银弹还是枷锁？Claude Agent SDK 的架构真相
- Claude Code创始人亲授13条使用技巧
- Claude Code 内部工具开源 code-simplifier：终结 AI 屎山代码的终极方案
```
```

> 版权申明：内容来源网络，仅供学习研究，版权归原创者所有。如有侵权烦请告知，我们会立即删除并表示歉意。谢谢!

**架构师**

我们都是架构师！

![图片](images/img_011.jpeg)

****关注**架构师(JiaGouX)，添加“星标”**

**获取每天技术干货，一起成为牛逼架构师**

**技术群请****加若飞：****1321113940****进架构师群**

投稿、合作、版权等邮箱：**admin@137x.com**

