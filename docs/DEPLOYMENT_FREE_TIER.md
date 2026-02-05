# NYX 免费/共用生产部署方案（单机）

> 目标：在**无付费 SaaS**前提下，以最小成本完成可上线的自托管部署。

## 0) 适用范围

- 单台 Linux 服务器（或本地机器）即可运行。
- 适合 Testnet/Mainnet‑Equivalent 的最小生产环境。
- 需要 HTTPS 反代（推荐 Caddy 或 Nginx）。

---

## 1) 目录结构（示例）

```text
/opt/nyx
├─ apps/
├─ docs/
├─ nyx-world/               # Web Portal
├─ scripts/
├─ .env                     # 生产环境配置
└─ release_artifacts/
```

---

## 2) 构建 Web 产物

```bash
cd /opt/nyx/nyx-world
npm install
npm run build
```

> 产物输出：`/opt/nyx/nyx-world/dist`

---

## 3) 启动后端（systemd）

复制模板：

```bash
sudo cp deploy/free-tier/systemd/nyx-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable nyx-backend
sudo systemctl start nyx-backend
```

健康检查：

```bash
curl -sS http://127.0.0.1:8091/healthz | jq .
```

---

## 4) 启动指标导出器（systemd）

```bash
sudo cp deploy/free-tier/systemd/nyx-metrics.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable nyx-metrics
sudo systemctl start nyx-metrics
```

验证：

```bash
curl -sS http://127.0.0.1:9099/metrics | head -n 20
```

---

## 5) 反向代理（Caddy 推荐）

```bash
sudo mkdir -p /etc/caddy
sudo cp deploy/free-tier/caddy/Caddyfile /etc/caddy/Caddyfile
sudo systemctl restart caddy
```

说明：
- `file_server` 服务 Web 产物
- `/api/*` 与 `/ws/*` 反代到后端
- `/metrics` 可直出监控指标

---

## 6) HTTPS / 域名

- Caddy 自动申请证书（需要域名解析到服务器）
- Nginx 方案可替换为自有证书

---

## 7) 备份 / 灾备

建议每天执行：

```bash
export NYX_BACKUP_PASSPHRASE="your-strong-passphrase"
bash /opt/nyx/scripts/nyx_backup_encrypted.sh
```

恢复演练建议每周进行一次。

---

## 8) 关键环境变量

```bash
# 后端
export PYTHONPATH="/opt/nyx/apps/nyx-backend-gateway/src:/opt/nyx/apps/nyx-backend/src"
export NYX_GATEWAY_DB_PATH="/opt/nyx/apps/nyx-backend-gateway/data/nyx_gateway.db"

# 监控
export NYX_METRICS_LISTEN="127.0.0.1"
export NYX_METRICS_PORT="9099"
export NYX_METRICS_BASE_URL="http://127.0.0.1:8091"
```

---

如需高可用（多机/多活），可在后续添加：
- 反向代理多节点
- DB 主从 / 定期快照
- Prometheus + Grafana（自托管）
