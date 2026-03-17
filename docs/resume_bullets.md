## 中文版（可直接放简历）
- 基于 UCI Online Retail 交易数据搭建用户级实验分析项目，完成从数据清洗、指标设计、功效分析到 A/B Test 结果解读的端到端流程。
- 设计并实现实验质检模块，包括 SRM 检测、置信区间估计与 bootstrap 稳健性分析，输出转化率、订单数与 GMV 的实验结论。
- 使用 CUPED 对 GMV 指标进行方差缩减，提升实验灵敏度；并用 T-learner 进行异质性处理效应分析，识别高 uplift 细分人群。
- 在非随机投放场景下，基于倾向得分与 AIPW 估计优惠券策略的因果效应，对比 naive 结果与校正结果，形成定向投放建议。

## English version
- Built an end-to-end experimentation project on top of the UCI Online Retail dataset, covering data cleaning, metric design, power analysis, and A/B test readout at the customer level.
- Implemented experiment quality checks including SRM detection, confidence intervals, and bootstrap-based robustness analysis for conversion, orders, and GMV.
- Applied CUPED for variance reduction on GMV and used a T-learner framework to estimate heterogeneous treatment effects and identify high-uplift user segments.
- Estimated policy-targeted coupon effects in an observational setting using propensity scores and AIPW, contrasting naive correlations with adjusted causal estimates.
