# NYX 项目命令大全（中文说明）

> 目标：收录**与本项目相关的主要命令**，并用中文说明用途。  
> 说明：少数命令依赖本机环境（如 Xcode / Apple Developer 证书 / Node / Python）。

---

## 1) 仓库与基础

| 命令 | 作用 |
|---|---|
| `gh repo clone JiahaoAlbus/NYX-DIRTY-AND-DEVELOP` | 克隆主仓库。 |
| `git status -sb` | 查看当前修改与分支状态。 |
| `git log --oneline -5` | 查看最近 5 条提交。 |

---

## 2) 后端启动 / 健康检查

| 命令 | 作用 |
|---|---|
| `export PYTHONPATH="$(pwd)/apps/nyx-backend-gateway/src:$(pwd)/apps/nyx-backend/src"` | 配置后端 Python 模块路径。 |
| `python -m nyx_backend_gateway.server --host 127.0.0.1 --port 8091 --env-file .env.example` | 启动网关后端（本地）。 |
| `curl -sS http://127.0.0.1:8091/healthz | jq .` | 后端健康检查。 |
| `curl -sS http://127.0.0.1:8091/capabilities | jq .` | 查看能力开关（UI 渲染事实来源）。 |

---

## 3) 全链验证 / 证据链

| 命令 | 作用 |
|---|---|
| `bash scripts/nyx_verify_all.sh --seed 123 --run-id extreme-testnet` | 全链路验证（钱包/交易/聊天/商店/证据回放）。 |
| `bash scripts/nyx_pack_proof_artifacts.sh` | 打包 Proof 证据（proof tar.gz）。 |

---

## 4) 发布产物一键打包

| 命令 | 作用 |
|---|---|
| `bash scripts/build_release_artifacts.sh` | 生成 Web/Backend/Extension/iOS(模拟器)/Proof 全套产物。 |

---

## 5) Web Portal

| 命令 | 作用 |
|---|---|
| `cd nyx-world && npm install` | 安装 Web 依赖。 |
| `cd nyx-world && npm run dev` | 启动 Web 开发服务。 |
| `cd nyx-world && npm run build` | 构建 Web 生产包。 |
| `bash scripts/build_nyx_world.sh` | 生成 iOS WebBundle（供 App 内嵌）。 |

---

## 6) iOS（模拟器 / 真机 IPA）

| 命令 | 作用 |
|---|---|
| `bash scripts/build_ios_sim_app.sh` | 构建 iOS 模拟器 `.app`。 |
| `xcodebuild -project apps/nyx-ios/NYXPortal.xcodeproj -scheme NYXPortal -destination 'generic/platform=iOS Simulator' build` | 直接用 Xcodebuild 构建模拟器版本。 |
| `export NYX_IOS_TEAM_ID=YOUR_TEAM_ID` | 设置 Apple 开发团队 ID（真机签名必需）。 |
| `export NYX_IOS_EXPORT_METHOD=development` | 设置导出方式（development / ad-hoc / app-store / enterprise）。 |
| `bash scripts/build_ios_ipa.sh` | 生成可安装的 iPhone IPA（需签名）。 |

---

## 7) Browser Extension

| 命令 | 作用 |
|---|---|
| `zip -r release_artifacts/extension/nyx-extension.zip packages/extension` | 手动打包扩展（发布脚本会自动做）。 |

---

## 8) 安全 / “NO FAKE UI” 相关检查

| 命令 | 作用 |
|---|---|
| `bash scripts/check_no_fake_ui.sh` | 检查 Web 是否存在假按钮/假 UI。 |
| `python scripts/no_fake_code_check.py` | 代码层面 NO FAKE UI 检测。 |
| `python scripts/no_fake_gate_web.py` | Web 能力开关/假 UI 检测。 |
| `python scripts/nyx_ios_no_fake_gate.py` | iOS 假 UI / 能力开关检测。 |

---

## 9) 测试 / 验证脚本

| 命令 | 作用 |
|---|---|
| `python scripts/nyx_run_all_unittests.py` | 运行后端/脚本单元测试。 |
| `python scripts/nyx_smoke_all_modules.py` | 快速冒烟测试各模块。 |
| `node scripts/nyx_e2ee_dm_roundtrip.mjs` | E2EE DM 回环验证。 |
| `python scripts/verify_e2ee_storage.py` | 校验后端存储无明文。 |
| `bash scripts/nyx_fundraising_validate.sh` | 募资校验相关检查。 |

---

## 10) 复现 / 一键回归脚本（按需使用）

| 命令 | 作用 |
|---|---|
| `bash scripts/q7_repro_one_shot.sh` | Q7 相关一键复现。 |
| `python scripts/q8_repro_one_shot.py` | Q8 相关一键复现。 |
| `python scripts/q9_repro_one_shot.py` | Q9 相关一键复现。 |
| `python scripts/q10_repro_one_shot.py` | Q10 相关一键复现。 |

---

## 11) 开发辅助

| 命令 | 作用 |
|---|---|
| `bash scripts/nyx_backend_dev.sh` | 后端开发模式启动（快速本地调试）。 |

---

## 12) 环境变量（集成相关）

| 变量 | 作用 |
|---|---|
| `NYX_0X_API_KEY` | 0x Quote 集成。 |
| `NYX_JUPITER_API_KEY` | Jupiter Quote 集成。 |
| `NYX_MAGIC_EDEN_API_KEY` | Magic Eden 可选 key（上游接口可公开访问，但 key 可提速）。 |
| `NYX_PAYEVM_API_KEY` | PayEVM（当前未接入，等待官方端点/回调规范）。 |

---

如需补充具体命令（例如专用 CI、部署脚本、生产环境运维命令），告诉我范围即可继续扩展。
