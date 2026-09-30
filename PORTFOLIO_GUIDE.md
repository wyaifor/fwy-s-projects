# 作品集维护说明

## 入选规则

主导航只保留同时满足以下条件的项目：

1. 有可公开的完整代码、SQL、配置或可核验工作簿；
2. 有课程报告、保存输出或可复现验证记录；
3. 能明确说明项目性质、本人实际参与和 AI 辅助边界；
4. 不含个人信息、凭证、受限数据、第三方缓存或安全攻击材料。

## 当前主项目

| 分支 | 状态 | 公开内容 |
|---|---|---|
| `project/data-ev-charger-duckdb` | re-run verified / validation checked | Python、SQL、测试、验证摘要 |
| `project/responsible-ai-clip` | code and saved outputs checked | 多模态分析代码、配置、保存输出摘要 |
| `project/ml-car-price` | re-run verified | 决策树 Notebook、项目说明、复跑指标 |
| `project/bi-wdi-quality` | code and saved outputs checked | Tableau 工作簿、数据质量材料说明与 manifest |

## 不作为主导航的材料

- 仅有报告、课件或实验截图的本科作业；
- 个人分工无法核验的课程材料；
- 无法安全公开的安全研究材料；
- 缺少完整代码、报告或保存产出的目录。

这些内容不应作为招聘作品集的入口。若后续补齐可公开代码、报告和可核验输出，可重新评估是否纳入。

## 发布前检查

每次新项目进入主导航前，检查：

- `README.md` 是否说明目的、实际角色、数据/授权边界和复现步骤；
- `project-manifest.json` 是否记录公开材料及来源指纹；
- 是否移除了学号、邮箱、凭证、原始课程提交物和大型非必要数据；
- 是否避免将团队成果、AI 辅助实现或课程脚手架写成独立商业项目。
