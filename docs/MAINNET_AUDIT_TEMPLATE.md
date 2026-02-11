# Mainnet Security Audit Template (NYX)

> 目的：为第三方安全审计提供统一模板与交付要求。

## 1) 审计范围
- 组件：
  - Gateway (`apps/nyx-backend-gateway`)
  - Evidence backend (`apps/nyx-backend`)
  - Web portal (`nyx-world`)
  - iOS Shell (`apps/nyx-ios`)
  - Extension (`packages/extension`)
- 关键资产：证据链、交易执行、风控熔断、Web2 Guard

## 2) 威胁模型
- 资产与信任边界
- 攻击面清单
- 高风险假设（恶意输入、供应链、服务商失效）

## 3) 方法与标准
- 代码审计 + 静态分析 + 依赖扫描
- 关键路径手工审查（Evidence、Fees、Auth、Web2 Guard）
- 可复现的 PoC / exploit 验证
- 参考标准：OWASP ASVS / MASVS（如适用）

## 4) 交付物
- 审计报告（含风险分级、影响面、修复建议）
- PoC / 复现步骤（如有）
- 复测报告（修复后）
- 安全建议（运营、监控、部署）

## 5) 必交证据
- 提交哈希与构建产物校验
- Evidence/replay determinism 验证记录
- 风控与熔断策略配置（脱敏）
- CI/conformance 全绿截图或日志

## 6) 时间表
- 审计启动：
- 中期发现：
- 最终报告：
- 复测完成：

## 7) 免责与限制
审计仅覆盖约定范围。任何新增功能需触发增量审计或专项评估。
