# Claude Code 为什么缓存命中率能做到 92%？一篇讲清 Prompt Caching 的工程逻辑

> 公众号: 架构师
> 发布时间: 2026-04-21 23:22
> 原文链接: https://mp.weixin.qq.com/s/ZtrY372sjwSd4Yro5wUvKQ

---




架构师（JiaGouX）我们都是架构师！
架构未来，你来不来？

---

上个月写过一次 `Prompt Cache`，当时说的一句话现在回头看还是那样：Agent 真正难管的，落点在上下文，不在某个单独的提示词技巧。

具体可以见《[别把 Prompt Cache 只当优化技巧：它背后其实是 Agent 的架构纪律](https://mp.weixin.qq.com/s?__biz=MzAwNjQwNzU2NQ==&mid=2650408819&idx=1&sn=f0c65045a197c9a3a6ca5b19faeae4da&scene=21#wechat_redirect)》。

这两天刷到 Avi Chawla 一篇长文，把 Prompt Caching 从原理到落地讲得很透。我顺手把 Anthropic 的官方文档、Claude Code 成本页、Thariq 的帖子一起翻了一遍。

翻完觉得，这个题聊到现在，已经不只是"缓存能省多少钱"了。

**92% 缓存命中率，成本当然压下来了。但再往里看一层，这个数字更像是 Claude Code 怎么管上下文的一次侧写。**

这篇不翻译原文，也不打算写成 KV Cache 教程。就顺着工程现场的感觉往下聊：

- • 92% 到底说明了什么
- • KV Cache 到底缓存了什么
- • 一个 30 分钟会话里缓存怎么热起来的
- • 命中率靠哪几条纪律撑着
- • Prompt Caching 怎么就牵到了 Context Engineering
- • 自己做 Agent，哪几件事最该先动手

---

## 太长不看版

- • 92% 命中率的前提：Claude Code 把稳定内容和动态内容治理得很清楚——稳定前缀不乱动，动态尾部不乱涨。
- • Prompt Caching 复用的是模型处理前缀后留下来的 K/V 计算状态，不是上次的回答。匹配靠的是 token 序列级精确哈希，不是"语义相似"。
- • Anthropic 现在把 automatic caching 放到了很靠前的位置，缓存点会随着对话增长自动前移。
- • 缓存命中靠 exact prefix match。`tools -> system -> messages` 这个顺序被动一下，后面整段重算。
- • 文档补了几处容易忽略的细节：TTL 默认 5 分钟、可选 1 小时；自动 lookback 约 20 个 block；不同模型最小可缓存长度不一样；并发请求要等第一条响应开始后才能读到缓存。
- • Prompt Caching 更像 Context Engineering 的第一层地基。缓存管"别重复算"，上下文工程管"哪些东西根本不该一直背着"。
- • 做长任务 Agent，光会调模型不够。把 `CLAUDE.md` 瘦身、把专用规则移进 Skills、把冗长输出交给 hooks 和 subagents，比多写几段 Prompt 管用。

---

## 先聊聊这个 92%

前阵子 Claude Code 团队的 Thariq 发过一个帖子，标题很直接：`Prompt Caching Is Everything`。

这话有点标题党，但真跑过长任务 Agent 的人大概不会觉得夸张。两件事最容易失控：

- • 每一轮都要把老上下文重新算一遍
- • 上下文越滚越长，质量和成本一起往下掉

一旦真跑几十轮、上百轮，缓存就不是"后面有空再做"的优化项了，是必须先摆正的基本盘。

Thariq 帖子里有个拆法挺好的。Claude Code 的缓存布局大致分三层：

| 层级 | 典型内容 | 复用范围 | 我的理解 |
| --- | --- | --- | --- |
| 全局层（稳定前缀） | 系统提示词、工具定义 | 跨项目、跨会话 | 最贵的一段基础前缀，做成共享底座 |
| 项目层（稳定前缀） | `CLAUDE.md`、项目约定 | 同一项目内 | 项目知识别每次从零建立 |
| 动态尾部 | 当前任务历史、工具输出 | 随会话增长 | 新增量正常计费；较早的历史会随 breakpoint 前移逐步被缓存纳入 |

先看两张图，方便抓住后面的主线。

为什么长任务 Agent 会越跑越贵

![Image](output/wechat/Claude%20Code%20为什么缓存命中率能做到%2092_？一篇讲清%20Prompt%20Caching%20的工程逻辑/images/img_001.png)

*第一张图只说一件事：长任务真正贵的，往往不是输出长度，而是老前缀被每一轮重新 prefill。*

Claude Code 把上下文分成了 4 层

![Image](output/wechat/Claude%20Code%20为什么缓存命中率能做到%2092_？一篇讲清%20Prompt%20Caching%20的工程逻辑/images/img_002.png)

*第二张图接着往下走：先把上下文分层，缓存才有机会一直热着。*

图里我把 `CLAUDE.md` 单独拎了一层。严格说它最终还是落进 `system` 或 `messages` 的上下文序列里，但从工程治理看，它干的就是"项目级长期记忆"的活——把这层想清楚，后面缓存怎么设计就会顺很多。

所以我看 92% 这个数字，先注意到的其实不是数字本身。

是他们把稳定内容和动态内容治理得足够清楚。系统规则、项目规则属于稳定前缀，不乱动；任务历史、工具输出属于动态尾部，只往后长。没有一锅乱炖，也没有频繁改前缀把自己最该缓存的部分先弄碎。

说白了：

**Claude Code 先把"什么该稳定、什么该动态增长"这件事理清了，缓存才有空间持续命中。**

---

## 缓存复用的到底是什么

很多人第一次听到 Prompt Caching，直觉是"把上一次的回答存起来下次用"。

其实不是。

它复用的是模型处理前缀时算出来的中间计算状态，不是文本本身。

展开说一下。Transformer 在 prefill 阶段会为每个 token 算出三个向量：Query、Key、Value。注意力机制靠这三个向量来确定 token 之间的关系。其中 Key 和 Value 有一个很好的特性——**它们对某个 token 来说，只取决于它前面的 token，一旦算完就不会再变**。

所以如果两次请求的前缀完全一样，前一次算好的 K/V 张量下次可以直接用，不需要重算。

这就是 KV Cache 的核心逻辑：把这些 K/V 张量持久化到推理服务器上，用 **token 序列的密码学哈希值** 做索引。新请求进来，前缀的 hash 对上了，直接从内存加载，跳过 prefill。

注意，这里匹配的是 **token 序列级别的精确匹配**，不是"语义差不多"。这也是后面为什么顺序、序列化方式、模型都不能乱动的根本原因。

Anthropic 文档把缓存命中的前缀顺序写得很明确：`tools`、`system`、`messages`，从头到 cache breakpoint 的完整序列。

放到 Agent 场景里就是：每次请求虽然都会把整段上下文重新发过去，但只要前面那一大块 token 序列完全一致，模型就不用从头再算一次。

这个为什么值钱？得回到 LLM 推理的两段成本来看：

- • **prefill**：把整段输入吃进去，跑密集矩阵乘法，建立内部表示。计算密集，最贵。
- • **decode**：基于已有状态往后生成新 token。主要在读历史状态，相对便宜。

Prompt Caching 省的就是前面那段 prefill 反复算的钱。

但它不是"开了就省"。缓存写入（cache write）本身要付 1.25 倍溢价，读取（cache read）才是 0.1 倍。**本质是先为稳定前缀付一次更贵的写入成本，再靠后续多轮低价读把成本摊回来**。所以高命中率不是锦上添花，是这笔经济账成立的前提。

Avi 文里算了一笔很直观的账：假设静态前缀大约 20,000 token，会话跑 50 轮，这段没变过的内容会被反复处理到 100 万 token 的量级。账单上算得清清楚楚，用户那边却没得到任何新东西。

说直白点：

**长任务 Agent 最烧钱的地方，往往不是回答太长，而是每轮都在重新理解同一段老上下文。**

![Image](output/wechat/Claude%20Code%20为什么缓存命中率能做到%2092_？一篇讲清%20Prompt%20Caching%20的工程逻辑/images/img_003.png)

92% 命中率为什么能把成本压下来

*这张图把账重新收了一下：起作用的不是“模型忽然更便宜”，而是大头从 `base input` 挪到了 `cache read`。*

---

## 一个 30 分钟会话里，缓存到底怎么热起来的

光说"92% 很高"不太直观。Avi 文里按分钟拆了一个真实编码会话的账单变化，看完会清楚很多：

**第 0 分钟**：Claude Code 加载系统提示词、工具定义和项目的 `CLAUDE.md`。这段 payload 超过 20,000 token，每个 token 都是新的——这是整个会话里最贵的一刻。但你只付这一次。

**第 1–5 分钟**：你开始给指令，Claude Code 派 Explore 子智能体去读文件、跑 grep。这些工具输出都追加到动态尾部。但 20,000 token 的稳定前缀已经开始走 cache read，`$0.30/MTok` 而不是 `$3.00/MTok`。

**第 6–15 分钟**：Plan 子智能体接收的是摘要简报，不是原始的探索输出——因为把原始结果全塞进来会让动态尾部膨胀太快。计划出来了，你批准，Claude Code 开始改代码。每一轮都从缓存读稳定前缀，命中率爬过 90%，而且每次访问都会刷新 TTL，让缓存持续保持热度。

**第 16–25 分钟**：你又提了新需求，更多工具调用、更多终端输出。会话到这里已经处理了几十万 token，但 20,000 token 的基础层始终在缓存里。

**第 28 分钟**：在终端跑 `/cost`。如果没有缓存，200 万 token 按 Sonnet 4.5 费率算是 。缓存以1.15。**单个任务成本降了 81%。**

这个过程里有两个细节我留意了一下。

一个是 Plan 子智能体只吃摘要、不吃原始输出。缓存负责别重复算稳定前缀，摘要负责别让动态尾部膨胀太快——这两件事配合起来，才把成本压住了。

另一个是热缓存不是一次配好就行，是靠交互节奏维持的。会话一直在命中，TTL 就不断刷新。一旦中断超过 5 分钟没有请求，缓存过期，下次得重新写入。

---

## 92% 为什么能成立

大家容易记住一个数字：92%。

但工程上真正该记住的，是背后几条纪律。

### 1. 顺序得稳

Anthropic 文档写得很清楚：缓存前缀按 `tools -> system -> messages` 排。

这不是文风建议，是物理约束。

上游动一下，后面的 hash 全变了。缓存系统不管你"意思差不多"，它只认从开头开始的完整 token 序列。

Avi 文里有个例子很直观：

`1 + 2 = 3` 能命中缓存，`2 + 1 = 3` 直接 miss。

数学上一样，对缓存系统来说，序列变了就是变了。

缓存最怕什么

![Image](output/wechat/Claude%20Code%20为什么缓存命中率能做到%2092_？一篇讲清%20Prompt%20Caching%20的工程逻辑/images/img_004.png)

*这张图更适合拿来排查问题：顺序一变，前缀就变。真正省钱的动作，往往就是少去碰已经稳定下来的前缀。*

排查缓存命中的时候，我一般按这个顺序看：先看 `tools` 有没有被动过，再看 `system`，最后才看 `messages`。别一上来就怀疑模型"变笨了"，很多时候就是前缀被自己不小心改脏了。

补一句：`tools -> system -> messages` 是 API 层面的序列化顺序，也是缓存匹配的物理顺序。但从上下文管理角度看，记住一条就够了：**稳定的往前放，会变的往后长**。系统指令最稳定，放最前面；工具定义预先加载好，会话期间不增不删；参考文档保持稳定；对话历史和工具输出放最后面——这是动态尾部。

---

### 2. 前缀得干净

Thariq 提到过几个把缓存打碎的真实原因，对照文档看了一遍，逻辑完全一致：

- • 系统提示词里塞动态时间戳
- • 工具定义顺序不稳定
- • 会话中途修改工具参数
- • 中途切模型
- • 为了"切到某种模式"直接改 system prompt

文档把失效表补得更细了。除了工具定义变动会把整段缓存清掉之外，下面这些也会造成部分失效：

- • 开关 web search 或 citations，影响 system 层
- • 改 `tool_choice`、图片、thinking 参数，影响 message 层

这些东西平时看着像 API 边角料，真到生产里，都是能把账单拉高的坑。

### 3. 状态更新往后追加，别碰前缀

很多团队一开始图省事，"今天日期变了""进入 plan mode 了""刚有个文件被改过了"——直接改 system prompt。

短期方便，长期是自己把缓存最值钱的那一段先弄脏了。

Thariq 的建议很实在：这类更新写进下一条 message 或 tool result 就好，别碰前缀。

这个思路比"怎么写一个更聪明的 prompt"更管用。它护住的是系统的稳定底座。

---

## 文档里几处容易被忽略的细节

这次翻文档，发现几处平时容易跳过、到了实现层又很要命的东西。

### 自动缓存已经是一等公民了

现在 Anthropic 的 Prompt Caching 文档把 `automatic caching` 放到了很靠前的位置。

不用像早期那样到处手写 block-level `cache_control`。请求顶层放一个 `cache_control`，系统自动把 breakpoint 放到"最后一个可缓存 block"，随着对话增长自动前移。

多轮会话用起来很顺——不用每轮手动追 breakpoint，系统自己帮你把旧内容从缓存读、新内容往后写。

### lookback 有上限

文档补了一条很多帖子没提的限制：自动向前 lookback 只有大约 20 个 content blocks。

两个推论：

- • 对话增长太快，距离上一次缓存写入点超过 20 blocks，lookback 可能够不着。
- • 前面很多 block 长期稳定的话，有时候得主动加额外 breakpoint，别把命中全押在最后一个点上。

自动缓存好用，但不等于什么都不用管。

### 最小可缓存长度，不同模型不一样

不是加了 `cache_control` 就一定能缓存。文档写得更严格。

当前阈值按模型分：

- • Claude Opus 4.5/4.6/4.7 → 4096 tokens
- • Claude Sonnet 4.6 → 2048 tokens
- • Claude Sonnet 4.5/4/Opus 4.1 → 1024 tokens
- • Claude Haiku 4.5 → 4096 tokens

前缀本来就不长的话，缓存打不上去，不一定是代码写错了，可能就是没过阈值。

顺手补一下价格。按 Anthropic 当前价表，Claude Sonnet 4.5/4.6 base input `$3 / MTok`，5 分钟 cache write `$3.75 / MTok`，1 小时 cache write `$6 / MTok`，cache hits `$0.30 / MTok`。Avi 文里那组"200 万 token，原价约 6 美元，缓存后压到 1.15 美元"的账，在这个价表下是对得上的。

### 并发场景有个坑

文档里还有一句容易漏掉：缓存 entry 只有在第一条响应开始返回之后，后续请求才读得到。

单会话没啥影响，并发 agent 就很现实了。

想让一批并行子任务吃同一段热前缀，别在第一条请求刚发出去时就把后面的全打出去。至少等第一个响应开始返回，缓存才真正落下去。

---

## 从 Prompt Caching 往前走一步，就到了 Context Engineering

如果文章停在这，还是一篇"缓存怎么省钱"的技术帖。

但这次几份材料放在一起看完，越来越觉得 Prompt Caching 更像是 Context Engineering 的第一层地基。

Anthropic 去年有一篇《Effective context engineering for AI agents》，里面把这条线说得很清楚：

- • 上下文是有限资源
- • 每多一个 token，注意力预算就继续被稀释
- • 好的上下文工程，目标不是把东西塞满，是找出最小的一组高信号 token

里面有几个点挺实在的。

一个是 Claude Code 走的 hybrid 路线：`CLAUDE.md` 这类基础材料直接放进上下文，文件探索、数据查看、`grep`/`glob` 交给运行时按需取。另一个是长任务要靠 compaction、note-taking、sub-agent architectures 一起配合，不能只指望窗口越来越大。

这两点跟 Prompt Caching 其实是连着的。

缓存解决的是"别把稳定内容反复重算"。

Context Engineering 再往下走一层：

- • 哪些内容该长期稳定
- • 哪些该按需取
- • 哪些该压缩
- • 哪些干脆别放进主会话

拉远看，它们是同一条链上的不同层。

Tobi 去年那句"`context engineering` 比 `prompt engineering` 更贴切"，我觉得说到点上了。做到最后，拼的是你能不能把任务需要的上下文摆到对的位置。

Alex Iskold 后来补了一条边界也有意思：`context engineering != process engineering`。

缓存和上下文工程，管的是"模型看到什么"。但业务流程本身——任务拆得乱、状态机设计得乱、工具职责交叉——这些缓存管不了。

---

## 落地的话，这 7 件事我会先查

别把动作收窄成"去把 `cache_control` 打开"就完事了。那当然要做，但远远不够。

已经有 Agent 在跑的话，从这 7 件事查起比较实在。

**1. 把前缀分层画出来。**

至少画清楚全局层、项目层、会话层分别是什么。很多成本问题，画完图就已经找到病灶了。

**2. 先清理前缀里的动态噪音。**

时间戳、随机 ID、无序 JSON、会漂移的工具描述，都先排掉。

**3. 减少基础上下文的常驻负担。**

Claude Code 成本页写得很直接：`CLAUDE.md` 会在 session 开始时装入上下文。细节型工作流说明，更适合移进 Skills，按需加载。

**4. 控制工具集的密度。**

tool set 要小而清晰，功能重叠越少越好。Claude Code 成本页也提到：MCP tool definitions 默认 deferred，只有真正调用时才展开。轻列表、重按需，基础前缀能轻不少。

**5. 把冗长输出交给 hooks 和 subagents。**

成本页给过两个方向：hooks 先过滤日志，subagents 处理测试输出、文档抓取、长日志，主会话只接摘要。成本和稳定性通常都能一起改善。

**6. 监控缓存相关 usage 字段。**

至少盯住 `cache_creation_input_tokens`、`cache_read_input_tokens`、`input_tokens`。命中率公式也很简单：

`cache_read_input_tokens / (cache_read_input_tokens + cache_creation_input_tokens)`

像盯正常运行时间一样盯这个指标。Claude Code 团队给 cache hit rate 做了告警，这件事本来就该进观测面板。

**7. 把 compaction 当成架构动作来做，而且要 cache-safe。**

compaction 讲究的是保留什么、丢掉什么。但压缩的方式也很重要——别为了压缩去改前缀。正确做法是保持 system prompt、tools、已有对话历史不动，把压缩指令作为新消息追加到最后。这样缓存的前缀照样复用，只有压缩指令本身需要计费。

这 7 件事做下来，大概率会看到一个很实际的变化：

**很多成本降下来，不是模型便宜了，是系统终于不再替自己重复付费了。**

---

## 写在最后

这次把 Avi 的文章、官方文档和几条帖子放在一起翻完，最大的感受就一句：

**Prompt Caching 真的不太适合继续当"提示词技巧"来看了。**

它更像一面镜子。

前缀有没有分层、工具有没有管住、项目规则是不是太重、长任务有没有压缩和隔离——这些东西做得干净，缓存命中率自然就上去了，成本和延迟跟着掉下来。

92% 确实抓眼球。

但数字背后我更在意的，是那种节制感：哪些东西该固定，哪些该后移，哪些只在需要时再拿出来。

把这几条边界收好，Prompt Caching 才会从一个 API feature，慢慢长成能托住长任务 Agent 的工程纪律。

---

## 往期相关

- • [Agent Harness 综述：同一个模型，为什么做出来的 Agent 差这么远](https://mp.weixin.qq.com/s?__biz=MzAwNjQwNzU2NQ==&mid=2650409084&idx=1&sn=b8db9f9925f5dba578cfc7044981f25a&scene=21#wechat_redirect)
- [• 30分钟手搓 Agent：LLM + Tools + Loop + Memory 跑通最小闭环](https://mp.weixin.qq.com/s?__biz=MzAwNjQwNzU2NQ==&mid=2650409091&idx=1&sn=3c40343aefdf11fdb208588a44033e14&scene=21#wechat_redirect)
- • [Anthropic 的 Harness，已经进入新阶段：只用三招，开始从"补"转向"删"](https://mp.weixin.qq.com/s?__biz=MzAwNjQwNzU2NQ==&mid=2650408980&idx=1&sn=05c9ea7d54a893039d03a52062db9dcc&scene=21#wechat_redirect)
- • [1M 上下文不是终点：Anthropic 正在把 Claude Code 变成"上下文操作系统"](https://mp.weixin.qq.com/s?__biz=MzAwNjQwNzU2NQ==&mid=2650409066&idx=1&sn=e28eab3e566c87ef7ecc4dc50ade1f3f&scene=21#wechat_redirect)

---

## 参考来源

- • Anthropic 官方文档：`[Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)`
- • Anthropic 工程博客：`[Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)`
- • Claude Code 文档：`[Manage costs effectively](https://code.claude.com/docs/en/costs)`
- • Anthropic 公告：`[Prompt caching with Claude](https://claude.com/blog/prompt-caching)`
- • Avi Chawla：`[Prompt caching in LLMs, clearly explained](https://x.com/_avichawla/status/2044670188998803855)`
- • Thariq：`[Lessons from Building Claude Code: Prompt Caching Is Everything](https://x.com/trq212/status/2024574133011673516)`
- • Tobi Lütke：`[I really like the term "context engineering" over prompt engineering](https://x.com/tobi/status/1935533422589399127)`
- • Alex Iskold：`[Context engineering != process engineering](https://x.com/alexiskold/status/2025644437657772317)`

---

如喜欢本文，请点击右上角，把文章分享到朋友圈

如有想了解学习的技术点，请留言给若飞安排分享

**因公众号更改推送规则，请点“在看”并加“星标”第一时间获取精彩技术分享**

**·END·**

```
```
相关阅读：


- 刚刚，Claude Code“代码泄露”背后：如何重新看 Agent Harness
- 大家都在讲 Harness，但它到底该怎么理解
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

![图片](images/img_005.jpeg)