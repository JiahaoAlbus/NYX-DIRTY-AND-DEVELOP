# NYX 运维落地（免费/共用方案）

> 目标：在不引入重依赖的前提下，提供**免费可运行**的生产运维基线：监控/告警/备份/灾备。

---

## 1) 监控/告警（免费）

### 1.1 轻量告警（阈值型）

```bash
python scripts/nyx_monitor_local.py
```

支持环境变量：
- `NYX_MONITOR_BASE_URL`：后端地址（默认 `http://127.0.0.1:8091`）
- `NYX_GATEWAY_DB_PATH`：数据库路径（默认 `apps/nyx-backend-gateway/data/nyx_gateway.db`）
- `NYX_MONITOR_ALERT_WEBHOOK`：可选告警 Webhook（Discord/Slack/飞书均可用）
- `NYX_MONITOR_LOOKBACK_HOURS`：Web2 Guard 错误统计窗口（默认 24h）
- `NYX_MONITOR_MAX_WEB2_ERRORS`：Web2 Guard 错误阈值
- `NYX_MONITOR_MAX_FAILED_REPLAY`：Evidence replay 失败阈值
- `NYX_MONITOR_MAX_NEGATIVE_BALANCES`：负余额阈值
- `NYX_MONITOR_MAX_TRANSFER_AMOUNT`：单笔转账异常阈值

**建议**：将 `python scripts/nyx_monitor_local.py` 写入 `cron` 每 5 分钟执行。

### 1.2 指标导出器（更强监控）

提供 Prometheus 格式与 JSON 两种输出：

```bash
python scripts/nyx_metrics_exporter.py
curl -sS http://127.0.0.1:9099/metrics | head -n 30
curl -sS http://127.0.0.1:9099/metrics.json | jq .
```

支持环境变量：
- `NYX_METRICS_LISTEN`：监听地址（默认 `127.0.0.1`）
- `NYX_METRICS_PORT`：监听端口（默认 `9099`）
- `NYX_METRICS_CACHE_SECONDS`：采集缓存秒数（默认 `10`）
- `NYX_METRICS_TIMEOUT`：健康检查超时（默认 `3`）
- `NYX_METRICS_BASE_URL`：后端地址（默认 `http://127.0.0.1:8091`）
- `NYX_GATEWAY_DB_PATH`：数据库路径

覆盖指标示例：
- Wallet 余额/转账/费用
- 订单/成交/证据回放
- Store 购买/Listing
- Chat/Portal 会话
- Web2 Guard 错误统计

---

## 2) 备份 / 灾备（强加密）

加密备份（AES‑256‑GCM + PBKDF2）：

```bash
export NYX_BACKUP_PASSPHRASE="your-strong-passphrase"
bash scripts/nyx_backup_encrypted.sh
```

恢复：

```bash
export NYX_BACKUP_PASSPHRASE="your-strong-passphrase"
bash scripts/nyx_restore_encrypted.sh release_artifacts/backups/nyx-backup-XXXX.tar.gz.enc ./nyx_restore
```

备份内容默认包含：
- `apps/nyx-backend-gateway/data/nyx_gateway.db`
- `apps/nyx-backend-gateway/runs`
- `docs/evidence`

可通过 `NYX_BACKUP_PATHS` 增加额外目录。

可选增强参数：
- `NYX_BACKUP_PBKDF2_ITER`（默认 `1000000`）
- `NYX_BACKUP_PBKDF2_DIGEST`（默认 `sha512`）

---

## 3) 生产部署（免费/自托管）

推荐：单机自托管（免费，最低成本）。  
只需要一台可联网机器（本地 / 免费 VPS / 共享服务器）。

最小步骤：
1. 启动后端：`python -m nyx_backend_gateway.server`
2. 构建 Web：`npm run build`
3. 用任意静态服务器托管 Web（Nginx / Caddy / Python http.server）
4. 将 80/443 反向代理到后端端口（8091）

---

## 4) 关键要求摘要

- **监控**：API/DB/证据回放/负余额/异常转账全部覆盖（脚本已落地）。
- **备份**：强加密、可恢复（脚本已落地）。
- **灾备**：至少每日备份 + 定期恢复演练（人工流程）。

---

部署与 systemd 模板：
- `docs/DEPLOYMENT_FREE_TIER.md`

如需升级到商业监控（Prometheus/Grafana/Sentry/Datadog），可以在下一步提供接入配置。
