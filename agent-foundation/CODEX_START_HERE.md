# Agent开发工具：从这里开始

这是本项目现行信息入口。按下面的任务类型读取唯一正文；实施事实查源码，批准与下一步查当前任务。旧规格、研究和尝试从历史入口按需追溯。

## 按任务读取现行正文

只读本次任务相关行，无需逐份通读；下表只维护导航，不另抄进度或要求。

| 任务/问题 | 文档拥有的内容 | 什么时候读取 | 唯一正文 |
|---|---|---|---|
| 继续、看批准/阻断、安排下一步 | 当前分期、确认状态、子任务依赖、实际结果与缺口 | 新session接续或推进应用任务 | [当前工作](docs/current/当前工作.md) |
| 新功能或范围调整 | 完整22项能力、16类对象、适用原则、例子及费用/数据/证据约束 | 发起新工作或检查是否改变目标 | [产品需求](docs/current/产品需求.md) |
| 创建Agent、修改、恢复、共享扩展 | 工作步骤、十项分类合同、产物/消费者与交付方法 | 已明确任务后规划和执行 | [开发方法](docs/current/开发方法.md) |
| review或实现构建首步 | T1—T5完整输入、操作、预期、失败和验证方法 | 修改验收或准备对应实现/验证 | [第1步验收](docs/current/第1步验收.md) |
| 理解为什么，重审架构/版本管理 | 有效持久决定、理由、职责与重审条件 | 重要取舍或可能推翻既有决定时 | [设计决定](docs/current/设计决定.md) |
| 查改动落点、学习调用关系 | 概念分层、按问题查代码、业务/共享边界与练习 | 改代码或理解实际结构时 | [架构与修改](docs/current/架构与修改.md) |
| 检查、打开页面、重载、停止、排错 | 工作目录/环境、操作顺序、失败定位和资源归属 | 实际操作前或遇错时 | [使用与排错](docs/current/使用与排错.md) |
| 设计测试、解释得分或接入写操作 | 分层取证、独立预期、诊断及执行边界 | 判断什么算通过、失败或未验证时 | [验证与安全](docs/current/验证与安全.md) |
| 避免概念混用 | 项目与运行/验证术语定义 | 出现术语歧义或教学需要时 | [术语](docs/current/术语.md) |
| 新写/更新/合并/清理文档 | 必要性、唯一归属、结构化改写和历史规则 | 修改项目资料及交接时 | [文档维护](docs/current/文档维护.md) |

## 原生资产与专用入口

下列文件有实际加载或特定操作消费者，保持其原格式；表格只定位，运行时规则和资料正文不复制到管理文档。普通任务读取现行正文；触及对应业务或操作才读这些文件。

| 读取条件 | 原生来源及内容职责 |
|---|---|
| 需要适用项目工程约束 | [项目指令](AGENTS.md)：现行项目指令与权限约束 |
| 改全部Agent的共同运行指令 | [base_instructions.md](foundation/base_instructions.md) |
| 改业务目标或引用要求 | [knowledge_helper指令](agents/knowledge_helper/instructions.md)、[support_insights指令](agents/support_insights/instructions.md) |
| 查资料问答实际依据 | [合成手册](agents/knowledge_helper/data/handbook.md)；业务检索消费者及引用以实际源码为准 |
| 修改生成模板 | [模板指令](agents/_template/instructions.md)、[data说明](agents/_template/data/README.md)、[knowledge说明](agents/_template/knowledge/README.md)、[skills说明](agents/_template/skills/README.md)、[workflows说明](agents/_template/workflows/README.md)；目录存在不等于加载能力 |
| 重复真实目录页验证 | [verify-agent-catalog](.agents/skills/verify-agent-catalog/SKILL.md)→[场景索引](.agents/skills/verify-agent-catalog/features/README.md)→[场景驱动](.agents/skills/verify-agent-catalog/features/catalog.md) |
| 查字段、参数、版本、实际分支 | 从[架构与修改的代码导航](docs/current/架构与修改.md#按问题找代码)进入真实代码/配置及相关测试，不手抄实现清单 |

## 历史追溯

仅当核查旧批准/接受、重大选择原因、失败现场、许可或恢复版本时，进入[历史目录](history/README.md)。有效结论已由上面的现行正文承接，历史不作为日常任务的必读前置。
