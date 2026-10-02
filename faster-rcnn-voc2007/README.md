# Faster R-CNN 目标检测与误差分析

> 课程小组项目｜公开版本已移除小组成员学号。

## 项目内容

基于 PASCAL VOC 2007 的 20 类目标检测任务，报告使用 COCO 预训练的 Faster R-CNN ResNet-50 FPN v2 进行微调，并以官方测试集完成类别 AP 与失败案例分析。

- 数据划分：训练 2,501 张、验证 2,510 张、测试 4,952 张图像。
- 训练设置：batch size 2、8 个 epoch、学习率 0.005、SGD momentum 0.9、weight decay 0.0005、StepLR 每 4 个 epoch 衰减。
- 结果口径：使用最佳验证检查点，在 IoU=0.50、置信度阈值=0.50 下，测试集 mAP@0.5 为 79.15%。
- 误差观察：模型在清晰的中大型目标上表现较好；小目标、遮挡与拥挤场景仍是主要困难。

## 文件说明

- [Assignment_Report.ipynb](Assignment_Report.ipynb)：课程报告与可视化代码，保留历史输出。
- [project-manifest.json](project-manifest.json)：公开范围、文件指纹与复现边界。

## 角色与边界

这是小组课程成果。候选人在简历中仅以课程小组成员身份引用整体实验结果，不将模型训练、指标或交付写作个人独立成果。该 notebook 依赖 PASCAL VOC 2007 数据集、PyTorch 与可用 GPU；公开仓库不包含数据集、模型权重或本地运行环境，因此不承诺开箱即完整复现。
