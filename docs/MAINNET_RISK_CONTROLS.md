# Mainnet Risk Controls & Circuit Breakers

> 目标：在主网环境中对共享状态变更实施风控与熔断，不影响确定性证据路径。

## 1) 设计原则
- 风控在**执行前**触发，阻断异常请求（不进入确定性证据路径）。
- 所有风控状态均可由配置驱动，不引入隐藏后门。
- 熔断为短期保护措施，恢复需人工确认或自动窗口过期。

## 2) 风控模式
`NYX_RISK_MODE`：`off | monitor | enforce`
- `off`：不拦截，仅适用于开发环境。
- `monitor`：记录与告警，不阻断。
- `enforce`：触发即拒绝（生产推荐）。

## 3) 风控配置（环境变量）
核心参数（详见 `.env.example`）：
- `NYX_RISK_GLOBAL_MUTATIONS_PAUSED`：全局熔断开关（紧急停写）
- `NYX_RISK_GLOBAL_MAX_PER_MIN` / `NYX_RISK_GLOBAL_MAX_AMOUNT_PER_MIN`
- `NYX_RISK_ACCOUNT_MAX_PER_MIN` / `NYX_RISK_ACCOUNT_MAX_AMOUNT_PER_MIN`
- `NYX_RISK_IP_MAX_PER_MIN` / `NYX_RISK_IP_MAX_AMOUNT_PER_MIN`
- 交易类：
  - `NYX_RISK_TRANSFER_MAX_PER_MIN`
  - `NYX_RISK_MAX_TRANSFER_AMOUNT`
  - `NYX_RISK_EXCHANGE_ORDERS_PER_MIN`
  - `NYX_RISK_MAX_ORDER_NOTIONAL`
- 商城类：
  - `NYX_RISK_MARKETPLACE_ORDERS_PER_MIN`
  - `NYX_RISK_MAX_STORE_NOTIONAL`
- 水龙头/空投：
  - `NYX_RISK_FAUCET_MAX_PER_MIN`
  - `NYX_RISK_MAX_FAUCET_AMOUNT`
  - `NYX_RISK_AIRDROP_MAX_PER_MIN`
  - `NYX_RISK_MAX_AIRDROP_AMOUNT`
- 聊天：
  - `NYX_RISK_CHAT_MESSAGES_PER_MIN`

## 4) 熔断规则
自动熔断（错误爆发）：
- `NYX_RISK_BREAKER_ERRORS_PER_MIN`
- `NYX_RISK_BREAKER_WINDOW_SECONDS`

当单个 action 在窗口内错误数超过阈值时：
- 该 action 自动进入熔断
- 窗口结束后自动解除（如需手动持续，使用全局开关）

## 5) 运行时行为
- 触发风控时返回 `HTTP 429` + 错误码 `RISK_LIMIT`
- `monitor` 模式仅记录日志
- 所有风控拒绝在证据链生成之前发生

## 6) 运维建议
- 主网启动时先 `monitor` 观测 7~14 天，再切换 `enforce`
- 与 `docs/OPERATIONAL_READINESS.md` 的告警联动
- 风控阈值应与业务指标（交易额/用户规模）动态调整
