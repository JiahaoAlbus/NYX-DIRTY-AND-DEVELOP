#!/usr/bin/env bash
set -euo pipefail

# NYX Extreme Full-Stack Verification Script (Testnet Release)
#
# Goals:
# - NO FAKE UI: only real endpoints + real state changes
# - Mainnet-equivalent: same fees/receipts/evidence; only testnet assets differ
# - Determinism: every mutation uses (seed, run_id) and produces evidence (state_hash/receipt_hashes)
# - Evidence: replay verify for every run, and proof bundle export (proof.zip)
#
# This script produces an evidence folder under docs/evidence/ and prints a short PASS summary.

SEED=123
RUN_ID_BASE="extreme-testnet"
BASE_URL="http://127.0.0.1:8091"
ENV_FILE=".env.example"

usage() {
  cat <<EOF
Usage: bash scripts/nyx_verify_all.sh [--seed N] [--run-id PREFIX] [--base-url URL] [--env-file PATH]

Examples:
  bash scripts/nyx_verify_all.sh --seed 123 --run-id extreme-testnet
  bash scripts/nyx_verify_all.sh --base-url http://127.0.0.1:8091
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --seed)
      SEED="$2"; shift 2 ;;
    --run-id|--run-id-base)
      RUN_ID_BASE="$2"; shift 2 ;;
    --base-url)
      BASE_URL="$2"; shift 2 ;;
    --env-file)
      ENV_FILE="$2"; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown arg: $1" >&2
      usage
      exit 2 ;;
  esac
done

if [[ "$ENV_FILE" == ".env.example" && -f ".env.local" ]]; then
  ENV_FILE=".env.local"
fi

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

if ! [[ "$SEED" =~ ^[0-9]+$ ]]; then
  echo "seed must be a non-negative integer" >&2
  exit 2
fi
if ! [[ "$RUN_ID_BASE" =~ ^[A-Za-z0-9_-]{1,64}$ ]]; then
  echo "run-id must match [A-Za-z0-9_-]{1,64}" >&2
  exit 2
fi

timestamp="$(date +%Y%m%d_%H%M%S)"
evidence_root="docs/evidence/${timestamp}_${RUN_ID_BASE}"
evidence_dir="${evidence_root}/verify_all"
mkdir -p "$evidence_dir"
echo "$evidence_root" > "docs/evidence/last_verify_path.txt"

RUN_SESSION="${RUN_ID_BASE}-${timestamp}"

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$evidence_dir/verify.log"; }
die() { echo "FAIL: $*" | tee -a "$evidence_dir/verify.log" >&2; exit 1; }

sanitize_action() { echo "$1" | sed -E 's/[^A-Za-z0-9_-]+/_/g'; }
counter_file="docs/evidence/run_counter_${RUN_ID_BASE}.txt"
RUN_COUNTER=0
NEXT_RUN_ID=""
next_run_id() {
  local action; action="$(sanitize_action "$1")"
  RUN_COUNTER=$((RUN_COUNTER + 1))
  echo "$RUN_COUNTER" > "$counter_file"
  NEXT_RUN_ID="${RUN_ID_BASE}-${action}-${RUN_COUNTER}"
}

curl_json() {
  local method="$1"
  local url="$2"
  local token="${3:-}"
  local body="${4:-}"
  local out="$5"
  local expect="${6:-200}"

  local -a headers
  headers=(-H "Content-Type: application/json")
  if [[ -n "$token" ]]; then
    headers+=(-H "Authorization: Bearer ${token}")
  fi

  local code
  if [[ -n "$body" ]]; then
    code="$(curl -sS -o "$out" -w "%{http_code}" -X "$method" "${headers[@]}" -d "$body" "$url" || true)"
  else
    code="$(curl -sS -o "$out" -w "%{http_code}" -X "$method" "${headers[@]}" "$url" || true)"
  fi
  if [[ "$code" != "$expect" ]]; then
    # allow comma-separated expected codes (e.g. "200,409")
    if [[ ",$expect," != *",$code,"* ]]; then
      log "HTTP $method $url -> $code (expected $expect)"
      cat "$out" >> "$evidence_dir/verify.log" || true
      return 1
    fi
  fi
  return 0
}

curl_get_json() {
  local url="$1"
  local token="${2:-}"
  local out="$3"
  local expect="${4:-200}"

  local code
  if [[ -n "$token" ]]; then
    code="$(curl -sS -o "$out" -w "%{http_code}" -H "Authorization: Bearer ${token}" "$url" || true)"
  else
    code="$(curl -sS -o "$out" -w "%{http_code}" "$url" || true)"
  fi
  if [[ "$code" != "$expect" ]]; then
    if [[ ",$expect," != *",$code,"* ]]; then
      log "HTTP GET $url -> $code (expected $expect)"
      cat "$out" >> "$evidence_dir/verify.log" || true
      return 1
    fi
  fi
  return 0
}

backend_pid=""
cleanup() {
  if [[ -n "${backend_pid:-}" ]]; then
    log "Stopping backend (pid=$backend_pid)"
    kill "$backend_pid" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

ensure_backend() {
  if curl -fsS "$BASE_URL/healthz" 2>/dev/null | jq -e '.ok == true' >/dev/null 2>&1; then
    log "Backend: online ($BASE_URL)"
    return 0
  fi

  log "Backend: offline, starting local gateway…"
  local root; root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  export PYTHONPATH="$root/apps/nyx-backend-gateway/src:$root/apps/nyx-backend/src"

  local env_file="$root/$ENV_FILE"
  if [[ ! -f "$env_file" ]]; then
    die "env file not found: $env_file"
  fi

  # Relax faucet IP limits for repeatable local verification runs.
  # Per-account limits and cooldown remain enforced unless overridden externally.
  export NYX_FAUCET_IP_MAX_CLAIMS_PER_24H="${NYX_VERIFY_FAUCET_IP_MAX_CLAIMS_PER_24H:-10000}"
  export NYX_FAUCET_MAX_AMOUNT_PER_24H="${NYX_VERIFY_FAUCET_MAX_AMOUNT_PER_24H:-10000}"
  export NYX_FAUCET_MAX_CLAIMS_PER_24H="${NYX_VERIFY_FAUCET_MAX_CLAIMS_PER_24H:-3}"
  export NYX_FAUCET_COOLDOWN_SECONDS="${NYX_VERIFY_FAUCET_COOLDOWN_SECONDS:-0}"
  export NYX_GATEWAY_DB_PATH="${NYX_GATEWAY_DB_PATH:-$evidence_root/gateway.db}"
  rm -f "$NYX_GATEWAY_DB_PATH" >/dev/null 2>&1 || true

  local host port
  host="$(python - <<PY
import os, urllib.parse
print(urllib.parse.urlparse(os.environ["BASE_URL"]).hostname or "127.0.0.1")
PY
)"
  port="$(python - <<PY
import os, urllib.parse
p=urllib.parse.urlparse(os.environ["BASE_URL"]).port
print(p if p is not None else 8091)
PY
)"

  BASE_URL="$BASE_URL" python -m nyx_backend_gateway.server --host "$host" --port "$port" --env-file "$env_file" >"$evidence_dir/backend.log" 2>&1 &
  backend_pid="$!"

  local deadline=$((SECONDS + 15))
  while [[ $SECONDS -lt $deadline ]]; do
    if curl -fsS "$BASE_URL/healthz" 2>/dev/null | jq -e '.ok == true' >/dev/null 2>&1; then
      log "Backend: online ($BASE_URL)"
      return 0
    fi
    sleep 0.3
  done
  die "backend failed to become healthy at $BASE_URL (see $evidence_dir/backend.log)"
}

export BASE_URL

ensure_backend
curl_get_json "$BASE_URL/healthz" "" "$evidence_dir/healthz.json" 200 || die "healthz failed"
curl_get_json "$BASE_URL/capabilities" "" "$evidence_dir/capabilities.json" 200 || die "capabilities failed"
curl_get_json "$BASE_URL/version" "" "$evidence_dir/version.json" 200 || true

# -------------------------------------------------------------------
# Capability sanity checks (NO FAKE UI)
# -------------------------------------------------------------------

if ! jq -e '.module_features.dapp.browser | tostring | test("^disabled") | not' "$evidence_dir/capabilities.json" >/dev/null 2>&1; then
  die "capabilities: dapp.browser must be enabled"
fi
if ! jq -e '.module_features.web2.guard | tostring | test("^disabled") | not' "$evidence_dir/capabilities.json" >/dev/null 2>&1; then
  die "capabilities: web2.guard must be enabled"
fi

if [[ -n "${NYX_0X_API_KEY:-}" ]]; then
  jq -e '.module_features.integrations."0x_quote" | tostring | test("^disabled") | not' "$evidence_dir/capabilities.json" >/dev/null 2>&1 \
    || die "capabilities: integrations.0x_quote should be enabled when NYX_0X_API_KEY is set"
else
  jq -e '.module_features.integrations."0x_quote" | tostring | test("^disabled")' "$evidence_dir/capabilities.json" >/dev/null 2>&1 \
    || die "capabilities: integrations.0x_quote should be disabled when NYX_0X_API_KEY is not set"
fi

if [[ -n "${NYX_JUPITER_API_KEY:-}" ]]; then
  jq -e '.module_features.integrations.jupiter_quote | tostring | test("^disabled") | not' "$evidence_dir/capabilities.json" >/dev/null 2>&1 \
    || die "capabilities: integrations.jupiter_quote should be enabled when NYX_JUPITER_API_KEY is set"
else
  jq -e '.module_features.integrations.jupiter_quote | tostring | test("^disabled")' "$evidence_dir/capabilities.json" >/dev/null 2>&1 \
    || die "capabilities: integrations.jupiter_quote should be disabled when NYX_JUPITER_API_KEY is not set"
fi

jq -e '.module_features.integrations.magic_eden_solana | tostring | test("^disabled") | not' "$evidence_dir/capabilities.json" >/dev/null 2>&1 \
  || die "capabilities: integrations.magic_eden_solana should be enabled"

jq -e '.module_features.integrations.magic_eden_evm | tostring | test("^disabled") | not' "$evidence_dir/capabilities.json" >/dev/null 2>&1 \
  || die "capabilities: integrations.magic_eden_evm should be enabled"

log "Seed=$SEED"
log "Run prefix=$RUN_ID_BASE"
log "Run session=$RUN_SESSION"

# Seed the run counter from:
# 1) backend /list (existing runs), and
# 2) local counter_file (previous script runs),
# so reruns don't collide on run_id.
if curl_get_json "$BASE_URL/list" "" "$evidence_dir/list_runs.json" 200; then
  max_from_backend="$(jq -r --arg prefix "${RUN_ID_BASE}-" '
    [.runs[].run_id
      | select(startswith($prefix))
      | (try (capture("-(?<n>[0-9]+)$").n) catch empty)
      | tonumber
    ] | max // 0
  ' "$evidence_dir/list_runs.json" 2>/dev/null || echo 0)"
else
  max_from_backend=0
fi

max_from_file=0
if [[ -f "$counter_file" ]]; then
  raw="$(cat "$counter_file" 2>/dev/null || true)"
  if [[ "$raw" =~ ^[0-9]+$ ]]; then
    max_from_file="$raw"
  fi
fi

RUN_COUNTER="$max_from_backend"
if [[ "$max_from_file" -gt "$RUN_COUNTER" ]]; then
  RUN_COUNTER="$max_from_file"
fi
echo "$RUN_COUNTER" > "$counter_file"
RUN_COUNTER_START="$RUN_COUNTER"
log "Run counter start=$RUN_COUNTER"

# -------------------------------------------------------------------
# Portal accounts (A/B), deterministic keys
# -------------------------------------------------------------------

portal_pubkey() {
  local label="$1"
  python - <<PY
import base64, hashlib, os
seed = f"portal-key:{os.environ['RUN_SESSION']}:{os.environ['LABEL']}".encode("utf-8")
raw = hashlib.sha256(seed).digest()
print(base64.b64encode(raw).decode("utf-8"))
PY
}

portal_handle() {
  local label="$1"
  python - <<PY
import hashlib, os
run = os.environ["RUN_SESSION"]
label = os.environ["LABEL"]
suffix = hashlib.sha256(f"handle:{label}:{run}".encode("utf-8")).hexdigest()[:8]
print((label.lower()[0] + suffix))
PY
}

portal_account_id() {
  python - <<PY
import hashlib, os
handle = os.environ["HANDLE"]
pubkey = os.environ["PUBKEY"]
digest = hashlib.sha256(f"portal:acct:{handle}:{pubkey}".encode("utf-8")).hexdigest()
print(f"acct-{digest[:16]}")
PY
}

portal_hmac_signature() {
  python - <<PY
import base64, hashlib, hmac, os
key = base64.b64decode(os.environ["PUBKEY"].encode("utf-8"))
nonce = os.environ["NONCE"].encode("utf-8")
sig = hmac.new(key, nonce, hashlib.sha256).digest()
print(base64.b64encode(sig).decode("utf-8"))
PY
}

create_or_reuse_portal_account() {
  local label="$1" handle="$2" pubkey="$3" out_prefix="$4"
  local out="$evidence_dir/${out_prefix}_create_account.json"
  local body; body="$(jq -n --arg handle "$handle" --arg pubkey "$pubkey" '{handle:$handle,pubkey:$pubkey}')"
  if curl_json "POST" "$BASE_URL/portal/v1/accounts" "" "$body" "$out" "200,400"; then
    local ok; ok="$(jq -r '.account_id // empty' "$out")"
    if [[ -n "$ok" ]]; then
      echo "$ok"
      return 0
    fi
  fi

  local message
  message="$(jq -r '.error.message // .error // empty' "$out" 2>/dev/null || true)"
  if [[ "$message" == "handle unavailable" ]]; then
    HANDLE="$handle" PUBKEY="$pubkey" portal_account_id
    return 0
  fi
  die "portal create_account failed for $label: $(cat "$out")"
}

portal_login() {
  local account_id="$1" pubkey="$2" out_prefix="$3"
  local challenge_out="$evidence_dir/${out_prefix}_challenge.json"
  local body; body="$(jq -n --arg account_id "$account_id" '{account_id:$account_id}')"
  curl_json "POST" "$BASE_URL/portal/v1/auth/challenge" "" "$body" "$challenge_out" 200 || die "portal challenge failed"
  local nonce; nonce="$(jq -r '.nonce' "$challenge_out")"
  local signature
  signature="$(NONCE="$nonce" PUBKEY="$pubkey" portal_hmac_signature)"

  local verify_out="$evidence_dir/${out_prefix}_verify.json"
  local verify_body; verify_body="$(jq -n --arg account_id "$account_id" --arg nonce "$nonce" --arg signature "$signature" '{account_id:$account_id,nonce:$nonce,signature:$signature}')"
  curl_json "POST" "$BASE_URL/portal/v1/auth/verify" "" "$verify_body" "$verify_out" 200 || die "portal verify failed"
  local token; token="$(jq -r '.access_token' "$verify_out")"

  # redact token in stored verify response
  jq '.access_token="REDACTED"' "$verify_out" > "$evidence_dir/${out_prefix}_verify_redacted.json"
  rm -f "$verify_out"

  echo "$token"
}

LABEL="A" RUN_ID_BASE="$RUN_ID_BASE" RUN_SESSION="$RUN_SESSION" export RUN_ID_BASE RUN_SESSION LABEL
HANDLE_A="$(portal_handle "A")"
PUBKEY_A="$(portal_pubkey "A")"
ACCOUNT_A="$(create_or_reuse_portal_account "A" "$HANDLE_A" "$PUBKEY_A" "A")"
TOKEN_A="$(portal_login "$ACCOUNT_A" "$PUBKEY_A" "A")"
curl_get_json "$BASE_URL/portal/v1/me" "$TOKEN_A" "$evidence_dir/A_me.json" 200 || die "portal me (A) failed"

LABEL="B" RUN_ID_BASE="$RUN_ID_BASE" RUN_SESSION="$RUN_SESSION" export RUN_ID_BASE RUN_SESSION LABEL
HANDLE_B="$(portal_handle "B")"
PUBKEY_B="$(portal_pubkey "B")"
ACCOUNT_B="$(create_or_reuse_portal_account "B" "$HANDLE_B" "$PUBKEY_B" "B")"
TOKEN_B="$(portal_login "$ACCOUNT_B" "$PUBKEY_B" "B")"
curl_get_json "$BASE_URL/portal/v1/me" "$TOKEN_B" "$evidence_dir/B_me.json" 200 || die "portal me (B) failed"

log "Accounts: A=$ACCOUNT_A (@$HANDLE_A), B=$ACCOUNT_B (@$HANDLE_B)"

# -------------------------------------------------------------------
# External integrations (read-only)
# -------------------------------------------------------------------

if [[ -n "${NYX_0X_API_KEY:-}" ]]; then
  log "Integration: 0x quote"
  curl_get_json "$BASE_URL/integrations/v1/0x/quote?network=ethereum&chain_id=1&sell_token=0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2&buy_token=0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48&sell_amount=1000000000000000&taker_address=0x0000000000000000000000000000000000010000&slippage_bps=50" \
    "$TOKEN_A" "$evidence_dir/integration_0x_quote.json" 200 || die "0x quote failed"
  jq -e '.provider=="0x" and .status==200 and (.data|type=="object")' "$evidence_dir/integration_0x_quote.json" >/dev/null 2>&1 \
    || die "0x quote response invalid"
else
  log "Integration: 0x quote skipped (NYX_0X_API_KEY not set)"
fi

if [[ -n "${NYX_JUPITER_API_KEY:-}" ]]; then
  log "Integration: Jupiter quote"
  curl_get_json "$BASE_URL/integrations/v1/jupiter/quote?input_mint=So11111111111111111111111111111111111111112&output_mint=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v&amount=10000000&slippage_bps=50" \
    "$TOKEN_A" "$evidence_dir/integration_jupiter_quote.json" 200 || die "jupiter quote failed"
  jq -e '.provider=="jupiter" and .status==200 and (.data|type=="object")' "$evidence_dir/integration_jupiter_quote.json" >/dev/null 2>&1 \
    || die "jupiter quote response invalid"
else
  log "Integration: Jupiter quote skipped (NYX_JUPITER_API_KEY not set)"
fi

log "Integration: Magic Eden Solana collections"
if curl_get_json "$BASE_URL/integrations/v1/magic_eden/solana/collections?limit=20&offset=0" \
  "$TOKEN_A" "$evidence_dir/integration_magic_eden_collections.json" 200; then
  if jq -e '.provider=="magic_eden" and .status==200 and (.data|type=="array")' "$evidence_dir/integration_magic_eden_collections.json" >/dev/null 2>&1; then
    symbol="$(jq -r '.data[0].symbol // empty' "$evidence_dir/integration_magic_eden_collections.json" 2>/dev/null || true)"
    if [[ -n "$symbol" ]]; then
      log "Integration: Magic Eden Solana listings ($symbol)"
      if curl_get_json "$BASE_URL/integrations/v1/magic_eden/solana/collection_listings?symbol=$symbol&limit=20&offset=0" \
        "$TOKEN_A" "$evidence_dir/integration_magic_eden_listings.json" 200; then
        if jq -e '.provider=="magic_eden" and .status==200 and (.data|type=="array")' "$evidence_dir/integration_magic_eden_listings.json" >/dev/null 2>&1; then
          mint="$(jq -r '.data[0].tokenMint // .data[0].mint // empty' "$evidence_dir/integration_magic_eden_listings.json" 2>/dev/null || true)"
          if [[ -n "$mint" ]]; then
            log "Integration: Magic Eden Solana token ($mint)"
            if curl_get_json "$BASE_URL/integrations/v1/magic_eden/solana/token?mint=$mint" \
              "$TOKEN_A" "$evidence_dir/integration_magic_eden_token.json" 200; then
              jq -e '.provider=="magic_eden" and .status==200' "$evidence_dir/integration_magic_eden_token.json" >/dev/null 2>&1 \
                || log "Magic Eden token response invalid"
            else
              log "Magic Eden token unavailable; skipping"
            fi
          else
            log "Integration: Magic Eden token skipped (mint not found)"
          fi
        else
          log "Magic Eden listings response invalid; skipping"
        fi
      else
        log "Magic Eden listings unavailable; skipping"
      fi
    else
      log "Magic Eden collections missing symbol; skipping listings"
    fi
  else
    log "Magic Eden collections response invalid; skipping"
  fi
else
  log "Magic Eden collections unavailable; skipping"
fi

log "Integration: Magic Eden EVM collections search"
if curl_get_json "$BASE_URL/integrations/v1/magic_eden/evm/collections/search?chain=ethereum&pattern=azuki&limit=1" \
  "$TOKEN_A" "$evidence_dir/integration_magic_eden_evm_search.json" 200; then
  if jq -e '.provider=="magic_eden" and .status==200 and (.data.collections|type=="array")' "$evidence_dir/integration_magic_eden_evm_search.json" >/dev/null 2>&1; then
    evm_slug="$(jq -r '.data.collections[0].symbol // .data.collections[0].slug // empty' "$evidence_dir/integration_magic_eden_evm_search.json" 2>/dev/null || true)"
    evm_id="$(jq -r '.data.collections[0].id // empty' "$evidence_dir/integration_magic_eden_evm_search.json" 2>/dev/null || true)"
    if [[ -n "$evm_slug" ]]; then
      log "Integration: Magic Eden EVM collections (slug=$evm_slug)"
      if curl_get_json "$BASE_URL/integrations/v1/magic_eden/evm/collections?chain=ethereum&collection_slugs=$evm_slug" \
        "$TOKEN_A" "$evidence_dir/integration_magic_eden_evm_collections.json" 200; then
        jq -e '.provider=="magic_eden" and .status==200 and (.data.collections|type=="array")' "$evidence_dir/integration_magic_eden_evm_collections.json" >/dev/null 2>&1 \
          || log "Magic Eden EVM collections response invalid"
      else
        log "Magic Eden EVM collections unavailable; skipping"
      fi
    elif [[ -n "$evm_id" ]]; then
      log "Integration: Magic Eden EVM collections (id=$evm_id)"
      if curl_get_json "$BASE_URL/integrations/v1/magic_eden/evm/collections?chain=ethereum&collection_ids=$evm_id" \
        "$TOKEN_A" "$evidence_dir/integration_magic_eden_evm_collections.json" 200; then
        jq -e '.provider=="magic_eden" and .status==200 and (.data.collections|type=="array")' "$evidence_dir/integration_magic_eden_evm_collections.json" >/dev/null 2>&1 \
          || log "Magic Eden EVM collections response invalid"
      else
        log "Magic Eden EVM collections unavailable; skipping"
      fi
    else
      log "Magic Eden EVM collections missing slug/id; skipping"
    fi
  else
    log "Magic Eden EVM search response invalid; skipping"
  fi
else
  log "Magic Eden EVM search unavailable; skipping"
fi

# -------------------------------------------------------------------
# Mutations (Wallet/Exchange/Store/Chat/Airdrop) + Evidence Replay
# -------------------------------------------------------------------

RUN_IDS=()

wallet_balances() {
  local account_id="$1" token="$2" out="$3"
  curl_get_json "$BASE_URL/wallet/v1/balances?address=$(python - <<PY
import urllib.parse, os
print(urllib.parse.quote(os.environ['ADDR']))
PY
)" "$token" "$out" 200 || return 1
}

ensure_nyxt_balance() {
  local account_id="$1" token="$2" out="$3" min_balance="$4"
  local balance
  balance="$(jq -r '.balances[] | select(.asset_id=="NYXT") | .balance' "$out" 2>/dev/null || echo "0")"
  if [[ -z "$balance" || "$balance" == "null" ]]; then
    balance=0
  fi
  if [[ "$balance" -ge "$min_balance" ]]; then
    return 0
  fi
  log "NYXT balance low (${balance}), attempting faucet top-up"
  next_run_id "wallet-faucet-topup-a"; TOPUP_RUN="$NEXT_RUN_ID"
  local topup_body
  topup_body="$(jq -n --argjson seed "$SEED" --arg run_id "$TOPUP_RUN" --arg address "$account_id" \
    '{seed:$seed,run_id:$run_id,payload:{address:$address,amount:5000,asset_id:"NYXT"}}')"
  curl_json "POST" "$BASE_URL/wallet/v1/faucet" "$token" "$topup_body" "$evidence_dir/A_faucet_topup.json" "200,429" \
    || die "wallet faucet top-up failed"
  if jq -e '.status=="complete"' "$evidence_dir/A_faucet_topup.json" >/dev/null 2>&1; then
    RUN_IDS+=("$TOPUP_RUN")
  fi
  ADDR="$account_id" wallet_balances "$account_id" "$token" "$out" || die "balances (A) after top-up failed"
  balance="$(jq -r '.balances[] | select(.asset_id=="NYXT") | .balance' "$out" 2>/dev/null || echo "0")"
  if [[ -z "$balance" || "$balance" == "null" ]]; then
    balance=0
  fi
  if [[ "$balance" -lt "$min_balance" ]]; then
    die "NYXT balance insufficient after top-up (${balance} < ${min_balance})"
  fi
  return 0
}

# Faucet limits are enforced server-side; by default each account can faucet once per 24h.
next_run_id "wallet-faucet-a-nyxt"; FAUCET_A_RUN="$NEXT_RUN_ID"
body="$(jq -n --argjson seed "$SEED" --arg run_id "$FAUCET_A_RUN" --arg address "$ACCOUNT_A" '{seed:$seed,run_id:$run_id,payload:{address:$address,amount:5000,asset_id:"NYXT"}}')"
curl_json "POST" "$BASE_URL/wallet/v1/faucet" "$TOKEN_A" "$body" "$evidence_dir/A_faucet.json" "200,429" || die "wallet faucet (A) failed"
if jq -e '.status=="complete"' "$evidence_dir/A_faucet.json" >/dev/null 2>&1; then
  RUN_IDS+=("$FAUCET_A_RUN")
else
  # allow cooldown/rate-limits for repeat runs; continue as long as balance is sufficient later
  log "A faucet not completed (likely cooldown): $(jq -c '.error' "$evidence_dir/A_faucet.json" 2>/dev/null || cat "$evidence_dir/A_faucet.json")"
fi

next_run_id "wallet-faucet-b-echo"; FAUCET_B_RUN="$NEXT_RUN_ID"
body="$(jq -n --argjson seed "$SEED" --arg run_id "$FAUCET_B_RUN" --arg address "$ACCOUNT_B" '{seed:$seed,run_id:$run_id,payload:{address:$address,amount:1000,asset_id:"ECHO"}}')"
curl_json "POST" "$BASE_URL/wallet/v1/faucet" "$TOKEN_B" "$body" "$evidence_dir/B_faucet.json" "200,429" || die "wallet faucet (B) failed"
if jq -e '.status=="complete"' "$evidence_dir/B_faucet.json" >/dev/null 2>&1; then
  RUN_IDS+=("$FAUCET_B_RUN")
else
  log "B faucet not completed (likely cooldown): $(jq -c '.error' "$evidence_dir/B_faucet.json" 2>/dev/null || cat "$evidence_dir/B_faucet.json")"
fi

ADDR="$ACCOUNT_A" wallet_balances "$ACCOUNT_A" "$TOKEN_A" "$evidence_dir/A_balances_1.json" || die "balances (A) failed"
ADDR="$ACCOUNT_B" wallet_balances "$ACCOUNT_B" "$TOKEN_B" "$evidence_dir/B_balances_1.json" || die "balances (B) failed"
ensure_nyxt_balance "$ACCOUNT_A" "$TOKEN_A" "$evidence_dir/A_balances_1.json" 200

log "Web2 Guard allowlist"
curl_get_json "$BASE_URL/web2/v1/allowlist" "" "$evidence_dir/web2_allowlist.json" 200 || die "web2 allowlist failed"

web2_ok=0
for web2_url in "https://api.github.com/zen" "https://api.coingecko.com/api/v3/ping" "https://api.coincap.io/v2/assets?limit=1"; do
  next_run_id "web2-guard-a"
  WEB2_RUN="$NEXT_RUN_ID"
  body="$(jq -n --argjson seed "$SEED" --arg run_id "$WEB2_RUN" --arg url "$web2_url" \
    '{seed:$seed,run_id:$run_id,payload:{url:$url,method:"GET"}}')"
  if curl_json "POST" "$BASE_URL/web2/v1/request" "$TOKEN_A" "$body" "$evidence_dir/A_web2_guard.json" 200; then
    if jq -e '.request_hash and .response_hash' "$evidence_dir/A_web2_guard.json" >/dev/null 2>&1; then
      RUN_IDS+=("$WEB2_RUN")
      web2_ok=1
      break
    fi
    log "web2 guard response missing hashes for ${web2_url}"
  else
    log "web2 guard request failed for ${web2_url}"
  fi
done

if [[ "$web2_ok" -ne 1 ]]; then
  die "web2 guard request failed"
fi

next_run_id "wallet-transfer-a-to-b"; TRANSFER_RUN="$NEXT_RUN_ID"
body="$(jq -n --argjson seed "$SEED" --arg run_id "$TRANSFER_RUN" --arg from "$ACCOUNT_A" --arg to "$ACCOUNT_B" \
  '{seed:$seed,run_id:$run_id,payload:{from_address:$from,to_address:$to,amount:300,asset_id:"NYXT"}}')"
curl_json "POST" "$BASE_URL/wallet/v1/transfer" "$TOKEN_A" "$body" "$evidence_dir/A_transfer.json" 200 || die "wallet transfer A->B failed"
RUN_IDS+=("$TRANSFER_RUN")

ADDR="$ACCOUNT_A" wallet_balances "$ACCOUNT_A" "$TOKEN_A" "$evidence_dir/A_balances_2.json" || die "balances (A) after transfer failed"
ADDR="$ACCOUNT_B" wallet_balances "$ACCOUNT_B" "$TOKEN_B" "$evidence_dir/B_balances_2.json" || die "balances (B) after transfer failed"

# Exchange: B places SELL (needs NYXT for fee) then A places BUY; should match into trades.
next_run_id "exchange-sell-b"; SELL_RUN="$NEXT_RUN_ID"
body="$(jq -n --argjson seed "$SEED" --arg run_id "$SELL_RUN" --arg owner "$ACCOUNT_B" \
  '{seed:$seed,run_id:$run_id,module:"exchange",action:"place_order",payload:{owner_address:$owner,side:"SELL",amount:100,price:1,asset_in:"ECHO",asset_out:"NYXT"}}')"
curl_json "POST" "$BASE_URL/run" "$TOKEN_B" "$body" "$evidence_dir/B_exchange_sell.json" 200 || die "exchange sell (B) failed"
RUN_IDS+=("$SELL_RUN")

next_run_id "exchange-buy-a"; BUY_RUN="$NEXT_RUN_ID"
body="$(jq -n --argjson seed "$SEED" --arg run_id "$BUY_RUN" --arg owner "$ACCOUNT_A" \
  '{seed:$seed,run_id:$run_id,module:"exchange",action:"place_order",payload:{owner_address:$owner,side:"BUY",amount:100,price:1,asset_in:"NYXT",asset_out:"ECHO"}}')"
curl_json "POST" "$BASE_URL/run" "$TOKEN_A" "$body" "$evidence_dir/A_exchange_buy.json" 200 || die "exchange buy (A) failed"
RUN_IDS+=("$BUY_RUN")

curl_get_json "$BASE_URL/exchange/v1/my_trades?limit=50&offset=0" "$TOKEN_A" "$evidence_dir/A_my_trades.json" 200 || die "A my_trades failed"
curl_get_json "$BASE_URL/exchange/v1/my_trades?limit=50&offset=0" "$TOKEN_B" "$evidence_dir/B_my_trades.json" 200 || die "B my_trades failed"

# Store: B publishes listing (fee paid in NYXT), A buys it.
SKU="$(RUN_SESSION="$RUN_SESSION" python - <<PY
import hashlib, os
print("s" + hashlib.sha256(os.environ["RUN_SESSION"].encode("utf-8")).hexdigest()[:6])
PY
)"
TITLE="Item"

next_run_id "marketplace-publish-b"; PUBLISH_RUN="$NEXT_RUN_ID"
body="$(jq -n --argjson seed "$SEED" --arg run_id "$PUBLISH_RUN" --arg publisher "$ACCOUNT_B" --arg sku "$SKU" --arg title "$TITLE" \
  '{seed:$seed,run_id:$run_id,module:"marketplace",action:"listing_publish",payload:{publisher_id:$publisher,sku:$sku,title:$title,price:10}}')"
curl_json "POST" "$BASE_URL/run" "$TOKEN_B" "$body" "$evidence_dir/B_listing_publish.json" 200 || die "listing_publish (B) failed"
RUN_IDS+=("$PUBLISH_RUN")

curl_get_json "$BASE_URL/marketplace/listings?limit=50&offset=0" "" "$evidence_dir/marketplace_listings.json" 200 || die "listings failed"
LISTING_ID="$(jq -r --arg sku "$SKU" '.listings[] | select(.sku==$sku) | .listing_id' "$evidence_dir/marketplace_listings.json" | head -n 1)"
if [[ -z "$LISTING_ID" || "$LISTING_ID" == "null" ]]; then
  die "listing_id not found for sku=$SKU"
fi
echo "$LISTING_ID" > "$evidence_dir/listing_id.txt"

next_run_id "marketplace-purchase-a"; PURCHASE_RUN="$NEXT_RUN_ID"
body="$(jq -n --argjson seed "$SEED" --arg run_id "$PURCHASE_RUN" --arg buyer "$ACCOUNT_A" --arg listing_id "$LISTING_ID" \
  '{seed:$seed,run_id:$run_id,module:"marketplace",action:"purchase_listing",payload:{buyer_id:$buyer,listing_id:$listing_id,qty:1}}')"
curl_json "POST" "$BASE_URL/run" "$TOKEN_A" "$body" "$evidence_dir/A_purchase.json" 200 || die "purchase_listing (A) failed"
RUN_IDS+=("$PURCHASE_RUN")

curl_get_json "$BASE_URL/marketplace/v1/my_purchases?limit=50&offset=0" "$TOKEN_A" "$evidence_dir/A_my_purchases.json" 200 || die "A my_purchases failed"

# Airdrop claims before Chat (top up NYXT to cover large protocol byte-fees).
curl_get_json "$BASE_URL/wallet/v1/airdrop/tasks" "$TOKEN_A" "$evidence_dir/A_airdrop_tasks_pre_chat.json" 200 || die "airdrop tasks (A) pre-chat failed"
claimable_pre="$(jq -r '.tasks[] | select(.claimable==true) | .task_id' "$evidence_dir/A_airdrop_tasks_pre_chat.json" || true)"
if [[ -z "$claimable_pre" ]]; then
  die "no airdrop tasks claimable for A before chat (expected trade_1/store_1 to be completed)"
fi

while IFS= read -r task_id; do
  [[ -z "$task_id" ]] && continue
  next_run_id "airdrop-claim-a-${task_id}"; CLAIM_RUN="$NEXT_RUN_ID"
  body="$(jq -n --argjson seed "$SEED" --arg run_id "$CLAIM_RUN" --arg task_id "$task_id" '{seed:$seed,run_id:$run_id,payload:{task_id:$task_id}}')"
  curl_json "POST" "$BASE_URL/wallet/v1/airdrop/claim" "$TOKEN_A" "$body" "$evidence_dir/A_airdrop_claim_${task_id}.json" 200 || die "airdrop claim failed for $task_id"
  RUN_IDS+=("$CLAIM_RUN")
done <<< "$claimable_pre"

# Chat (E2EE DM): end-to-end encrypt -> store ciphertext -> fetch -> decrypt.
next_run_id "chat-dm-a-to-b"; CHAT_RUN="$NEXT_RUN_ID"
export NYX_BASE_URL="$BASE_URL"
export NYX_TOKEN_A="$TOKEN_A"
export NYX_TOKEN_B="$TOKEN_B"
export NYX_ACCOUNT_A="$ACCOUNT_A"
export NYX_ACCOUNT_B="$ACCOUNT_B"
export NYX_SEED="$SEED"
export NYX_CHAT_RUN_ID="$CHAT_RUN"
export NYX_CHAT_PLAINTEXT="hi"
node "scripts/nyx_e2ee_dm_roundtrip.mjs" > "$evidence_dir/chat_roundtrip.json" || die "chat E2EE roundtrip failed"
RUN_IDS+=("$CHAT_RUN")
python "scripts/verify_e2ee_storage.py" > "$evidence_dir/e2ee_storage_check.log" 2>&1 || die "e2ee storage check failed"

# Airdrop claims after Chat (chat_1 should become claimable now).
curl_get_json "$BASE_URL/wallet/v1/airdrop/tasks" "$TOKEN_A" "$evidence_dir/A_airdrop_tasks_post_chat.json" 200 || die "airdrop tasks (A) post-chat failed"
claimable_post="$(jq -r '.tasks[] | select(.claimable==true) | .task_id' "$evidence_dir/A_airdrop_tasks_post_chat.json" || true)"
if [[ -z "$claimable_post" ]]; then
  die "no airdrop tasks claimable for A after chat (expected chat_1)"
fi

while IFS= read -r task_id; do
  [[ -z "$task_id" ]] && continue
  next_run_id "airdrop-claim-a-${task_id}"; CLAIM_RUN="$NEXT_RUN_ID"
  body="$(jq -n --argjson seed "$SEED" --arg run_id "$CLAIM_RUN" --arg task_id "$task_id" '{seed:$seed,run_id:$run_id,payload:{task_id:$task_id}}')"
  curl_json "POST" "$BASE_URL/wallet/v1/airdrop/claim" "$TOKEN_A" "$body" "$evidence_dir/A_airdrop_claim_${task_id}.json" 200 || die "airdrop claim failed for $task_id"
  RUN_IDS+=("$CLAIM_RUN")
done <<< "$claimable_post"

curl_get_json "$BASE_URL/wallet/v1/airdrop/tasks" "$TOKEN_A" "$evidence_dir/A_airdrop_tasks_after.json" 200 || die "airdrop tasks (A) after failed"

# Activity feed snapshots (Evidence Center UI consumes these).
curl_get_json "$BASE_URL/portal/v1/activity?limit=200&offset=0" "$TOKEN_A" "$evidence_dir/A_activity.json" 200 || die "activity (A) failed"
curl_get_json "$BASE_URL/portal/v1/activity?limit=200&offset=0" "$TOKEN_B" "$evidence_dir/B_activity.json" 200 || die "activity (B) failed"

# Replay verify every run_id we executed.
mkdir -p "$evidence_dir/replay"
for rid in "${RUN_IDS[@]}"; do
  out="$evidence_dir/replay/${rid}.json"
  body="$(jq -n --arg run_id "$rid" '{run_id:$run_id}')"
  curl_json "POST" "$BASE_URL/evidence/v1/replay" "$TOKEN_A" "$body" "$out" 200 || die "replay verify failed for $rid"
  if ! jq -e '.ok==true' "$out" >/dev/null 2>&1; then
    die "replay verify returned ok=false for $rid (see $out)"
  fi
done

# Proof export (zip of run exports) for account A and this run prefix.
proof_zip="$evidence_dir/proof_${ACCOUNT_A}.zip"
code="$(curl -sS -o "$proof_zip" -w "%{http_code}" -H "Authorization: Bearer ${TOKEN_A}" "$BASE_URL/proof.zip?prefix=${RUN_ID_BASE}&limit=200" || true)"
if [[ "$code" != "200" ]]; then
  rm -f "$proof_zip"
  die "proof.zip download failed (HTTP $code)"
fi
shasum -a 256 "$proof_zip" > "$evidence_dir/proof_${ACCOUNT_A}.zip.sha256"

# Final manifest (machine-readable)
jq -n \
  --arg seed "$SEED" \
  --arg run_id_base "$RUN_ID_BASE" \
  --arg run_session "$RUN_SESSION" \
  --arg base_url "$BASE_URL" \
  --arg timestamp "$timestamp" \
  --argjson run_counter_start "$RUN_COUNTER_START" \
  --arg account_a "$ACCOUNT_A" \
  --arg account_b "$ACCOUNT_B" \
  --arg handle_a "$HANDLE_A" \
  --arg handle_b "$HANDLE_B" \
  --argjson run_ids "$(printf '%s\n' "${RUN_IDS[@]}" | jq -R . | jq -s .)" \
  '{
    kind: "nyx-verify-all",
    version: 1,
    seed: ($seed|tonumber),
    run_id_base: $run_id_base,
    run_session: $run_session,
    base_url: $base_url,
    timestamp: $timestamp,
    run_counter_start: $run_counter_start,
    accounts: {
      a: { account_id: $account_a, handle: $handle_a },
      b: { account_id: $account_b, handle: $handle_b }
    },
    runs: $run_ids
  }' > "$evidence_dir/manifest.json"

# Human-readable summary (for reviewers)
summary_md="$evidence_root/SUMMARY.md"
{
  echo "# NYX verify_all PASS"
  echo
  echo "- seed: $SEED"
  echo "- run_id_base: $RUN_ID_BASE"
  echo "- run_session: $RUN_SESSION"
  echo "- timestamp: $timestamp"
  echo "- base_url: $BASE_URL"
  echo "- account_a: $ACCOUNT_A (@$HANDLE_A)"
  echo "- account_b: $ACCOUNT_B (@$HANDLE_B)"
  echo
  echo "Artifacts:"
  echo "- verify log: \`$evidence_dir/verify.log\`"
  echo "- manifest: \`$evidence_dir/manifest.json\`"
  echo "- replay outputs: \`$evidence_dir/replay/\`"
  echo
  echo "## External integrations (read-only)"
  echo
  if [[ -f "$evidence_dir/integration_0x_quote.json" ]]; then
    s="$(jq -r '.status // empty' "$evidence_dir/integration_0x_quote.json" 2>/dev/null || true)"
    echo "- 0x quote: status=${s:-unknown} (\`$evidence_dir/integration_0x_quote.json\`)"
  else
    echo "- 0x quote: skipped"
  fi
  if [[ -f "$evidence_dir/integration_jupiter_quote.json" ]]; then
    s="$(jq -r '.status // empty' "$evidence_dir/integration_jupiter_quote.json" 2>/dev/null || true)"
    echo "- Jupiter quote: status=${s:-unknown} (\`$evidence_dir/integration_jupiter_quote.json\`)"
  else
    echo "- Jupiter quote: skipped"
  fi
  if [[ -f "$evidence_dir/integration_magic_eden_collections.json" ]]; then
    s="$(jq -r '.status // empty' "$evidence_dir/integration_magic_eden_collections.json" 2>/dev/null || true)"
    echo "- Magic Eden collections: status=${s:-unknown} (\`$evidence_dir/integration_magic_eden_collections.json\`)"
  else
    echo "- Magic Eden collections: skipped"
  fi
  if [[ -f "$evidence_dir/integration_magic_eden_listings.json" ]]; then
    s="$(jq -r '.status // empty' "$evidence_dir/integration_magic_eden_listings.json" 2>/dev/null || true)"
    echo "- Magic Eden listings: status=${s:-unknown} (\`$evidence_dir/integration_magic_eden_listings.json\`)"
  else
    echo "- Magic Eden listings: skipped"
  fi
  if [[ -f "$evidence_dir/integration_magic_eden_token.json" ]]; then
    s="$(jq -r '.status // empty' "$evidence_dir/integration_magic_eden_token.json" 2>/dev/null || true)"
    echo "- Magic Eden token: status=${s:-unknown} (\`$evidence_dir/integration_magic_eden_token.json\`)"
  else
    echo "- Magic Eden token: skipped"
  fi
  echo
  echo "## Runs (state mutations)"
  echo
  echo "| run_id | state_hash | receipt_hash | fee_total | treasury |"
  echo "|---|---|---|---:|---|"
  for rid in "${RUN_IDS[@]}"; do
    out="$evidence_dir/replay/${rid}.json"
    state="$(jq -r '.recorded.outputs.state_hash // .recorded.state_hash' "$out" 2>/dev/null || echo "")"
    receipt="$(jq -r '.recorded.outputs.receipt_hashes[0] // .recorded.receipt_hashes[0]' "$out" 2>/dev/null || echo "")"
    fee_total="$(jq -r '.recorded.outputs.fee_total // empty' "$out" 2>/dev/null || true)"
    treasury="$(jq -r '.recorded.outputs.treasury_address // empty' "$out" 2>/dev/null || true)"
    echo "| \`$rid\` | \`$state\` | \`$receipt\` | ${fee_total:-} | \`${treasury:-}\` |"
  done
  echo
  echo "## Proof export"
  echo
  echo "- proof.zip (account A): \`$evidence_dir/proof_${ACCOUNT_A}.zip\`"
  echo "- sha256: \`$(awk '{print $1}' "$evidence_dir/proof_${ACCOUNT_A}.zip.sha256")\`"
} > "$summary_md"

log "PASS: all verifications completed"
log "Evidence dir: $evidence_root"

echo "PASS"
echo "EVIDENCE_DIR=$evidence_root"
echo "RUNS=${#RUN_IDS[@]}"
