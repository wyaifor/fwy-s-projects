# 冯婉怡｜项目作品集

本仓库按培养阶段整理。每个入口均说明项目性质、本人实际参与边界与复现条件；不会将课程脚手架、小组成果或 AI 辅助实现误写成独立商业项目。

## 研究生阶段｜2025.08–2027.03

这些项目有可公开的完整代码、课程报告、保存输出或复现验证记录，适合招聘阅读。

| 项目 | 适合岗位 | 已核验内容 | 本人实际角色 | 查看 |
|---|---|---|---|---|
| NSW EV 充电设施数据集成与 DuckDB 核验 | 数据产品、AI 产品、数据运营、项目交付 | 1,958 条源记录；9 张表、3 个视图；433 个 DC ID 完整保留；空间匹配与数据质量校验 | 负责最终集成与结果检查；实现与文档存在 AI 辅助 | [项目说明](https://github.com/wyaifor/fwy-s-projects/tree/project/data-ev-charger-duckdb) |
| CLIP 图文关联偏差与推荐模拟 | AI 产品、负责任 AI、数据分析 | 4,200 张样本图像、41 个职业标签、164 条提示词；代码与保存输出已核验 | 三人课程团队成员；负责排期、进度跟进与材料整合 | [项目说明](https://github.com/wyaifor/fwy-s-projects/tree/project/responsible-ai-clip) |
| 二手汽车价格预测与决策树解释 | 数据分析、产品策略、数据运营 | 8,107 条有效目标记录；5 折交叉验证、360 组候选参数；已完成窄范围复跑 | 决策树模块参与者；结果检查与协作，代码存在 AI 辅助 | [项目说明](https://github.com/wyaifor/fwy-s-projects/tree/project/ml-car-price) |
| 世界发展指标数据质量与 Tableau 可视化 | 数据运营、BI、经营分析 | 14,075 行面板数据、217 个国家、65 年、9 个指标、7 张工作表与 2 个仪表板 | 小组项目中的评估与一致性模块；个人报告部分已核验 | [项目说明](https://github.com/wyaifor/fwy-s-projects/tree/project/bi-wdi-quality) |
| Faster R-CNN 目标检测与误差分析 | AI 产品、数据分析、视觉 AI | VOC 2007：2,501/2,510/4,952 张训练、验证、测试图像；mAP@0.5 79.15%；报告与保存输出已核验 | 课程小组成员；仅以团队成果引用实验指标，不表述为个人独立训练 | [项目说明](https://github.com/wyaifor/fwy-s-projects/tree/project/cv-faster-rcnn-voc2007) |

### 研究生阶段阅读顺序

- 投递 **AI 产品、产品运营、数据产品**：先看 NSW EV，再看 CLIP。
- 投递 **数据运营、经营分析、BI**：先看 NSW EV、WDI 和二手汽车项目。
- 投递 **项目协调、交付或解决方案**：先看 NSW EV；其中的数据口径、核验和可追溯性最贴近业务交付。
- 投递 **AI 产品、视觉 AI 或模型评估相关岗位**：可补充阅读 Faster R-CNN；重点是实验评估、误差归因和可验证改进建议。

## 本科阶段｜2021.10–2025.07

本科材料以基础课程实验为主。目前保存的项目大多只有实验报告、截图或局部代码，尚无可公开的完整工程，因此不作为求职核心作品展示。为保留学习轨迹，以下列出具有明确主题的代表材料；后续补齐工程代码、报告和可核验输出后，才会升级为主项目。

| 课程材料 | 方向 | 当前状态 | 查看 |
|---|---|---|---|
| LangChain + ChatGLM 电子工艺实习智能问答系统（本科毕设） | 本地知识库问答、教育 AI | 论文与归档材料已核对；未发现完整源码，因此仅公开脱敏说明与报告口径，不承诺可复现 | [项目说明](https://github.com/wyaifor/fwy-s-projects/tree/project/undergrad-langchain-chatglm-electronic-qa) |
| 手势识别飞腾派开发板实现 | 智能感知与嵌入式 | 报告与截图已保存；未发现完整工程 | [材料说明](https://github.com/wyaifor/fwy-s-projects/tree/project/undergrad-03) |
| 单片机小车寻迹实验 | 嵌入式与控制 | 实验报告已保存；未发现完整工程 | [材料说明](https://github.com/wyaifor/fwy-s-projects/tree/project/undergrad-04) |
| 遗传算法设计与实现 | 机器学习基础 | 实验报告已保存；未发现可安全运行的完整工程 | [材料说明](https://github.com/wyaifor/fwy-s-projects/tree/project/undergrad-12) |

## 代码、报告与公开边界

每个项目分支含 `README.md`、`project-manifest.json`，以及可公开的代码、SQL、配置或已保存输出。原始课程报告、输入数据、学生信息、第三方服务缓存及授权不明材料不上传；其文件指纹与公开范围在 manifest 中保留。

详细筛选标准、发布前检查与后续入选规则见 [作品集维护说明](PORTFOLIO_GUIDE.md)。
