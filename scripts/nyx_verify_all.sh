#!/bin/bash
set -e

# NYX Testnet All-in-One Verification Script
# This script runs an end-to-end demo scenario and produces proof artifacts.

SEED=123
RUN_ID="verify-run-$(date +%s)"
BASE_URL="http://127.0.0.1:8091"
ARTIFACTS_DIR="release_artifacts/verify_logs"

mkdir -p "$ARTIFACTS_DIR"

echo "🔍 Starting NYX Full-Stack Verification..."
echo "Run ID: $RUN_ID"

# Helper for JSON extraction
get_val() {
    echo "$1" | grep -o "\"$2\":\"[^\"]*\"" | cut -d'"' -f4
}

# 1. Backend Health Check
echo "📡 Checking Backend Health..."
HEALTH=$(curl -s "$BASE_URL/healthz")
if [[ "$HEALTH" != *"\"ok\":true"* ]]; then
    echo "❌ Backend is offline or unhealthy."
    exit 1
fi
echo "✅ Backend is ONLINE."

# 2. Portal Account Creation
echo "👤 Creating Portal Account..."
HANDLE="u$(date +%s | cut -c 6-10)"
PUBKEY="dW51c2VkX3B1YmtleV9mb3JfdmVyaWZpY2F0aW9uX29ubHk=" # Base64 for "unused_pubkey_for_verification_only"
ACCOUNT_JSON=$(curl -s -X POST "$BASE_URL/portal/v1/accounts" -d "{\"handle\":\"$HANDLE\", \"pubkey\":\"$PUBKEY\"}")
ACCOUNT_ID=$(get_val "$ACCOUNT_JSON" "account_id")

if [ -z "$ACCOUNT_ID" ]; then
    echo "❌ Account creation failed: $ACCOUNT_JSON"
    exit 1
fi
echo "✅ Account Created: $ACCOUNT_ID (@$HANDLE)"

# 3. Auth Challenge & Verify
echo "🔑 Authenticating..."
CHALLENGE_JSON=$(curl -s -X POST "$BASE_URL/portal/v1/auth/challenge" -d "{\"account_id\":\"$ACCOUNT_ID\"}")
NONCE=$(get_val "$CHALLENGE_JSON" "nonce")

# Simulating HMAC signature (In real usage, this happens client-side)
# Key = "unused_pubkey_for_verification_only" (decoded)
# Signature = HMAC-SHA256(key, nonce)
# For simplicity in this script, we'll assume the backend allows a bypass or we implement the HMAC here.
# Actually, I'll just use a test-only bypass if I implement one, or use a python helper.

SIGNATURE=$(python3 -c "import hmac, hashlib, base64; key=base64.b64decode('$PUBKEY'); sig=hmac.new(key, '$NONCE'.encode(), hashlib.sha256).digest(); print(base64.b64encode(sig).decode())")

VERIFY_JSON=$(curl -s -X POST "$BASE_URL/portal/v1/auth/verify" -d "{\"account_id\":\"$ACCOUNT_ID\", \"nonce\":\"$NONCE\", \"signature\":\"$SIGNATURE\"}")
TOKEN=$(get_val "$VERIFY_JSON" "access_token")

if [ -z "$TOKEN" ]; then
    echo "❌ Authentication failed: $VERIFY_JSON"
    exit 1
fi
echo "✅ Authenticated. Token acquired."

# 4. Faucet Claim
echo "🚰 Claiming Faucet..."
FAUCET_JSON=$(curl -s -X POST "$BASE_URL/wallet/faucet" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"seed\":$SEED, \"run_id\":\"$RUN_ID-faucet\", \"payload\":{\"address\":\"$ACCOUNT_ID\", \"amount\":1000}}")
echo "$FAUCET_JSON" > "$ARTIFACTS_DIR/faucet_res.json"

if [[ "$FAUCET_JSON" != *"\"status\":\"complete\""* ]]; then
    echo "❌ Faucet claim failed."
    exit 1
fi
echo "✅ Faucet Claimed. Receipt: $(get_val "$FAUCET_JSON" "run_id")"

# 5. Check Balance
echo "💰 Checking Balance..."
BALANCE_JSON=$(curl -s "$BASE_URL/wallet/balance?address=$ACCOUNT_ID")
if [[ "$BALANCE_JSON" != *"\"balance\":1000"* ]]; then
    echo "❌ Balance check failed: $BALANCE_JSON"
    exit 1
fi
echo "✅ Balance Verified: 1000 NYXT"

# 6. Place Order
echo "📈 Placing Order..."
ORDER_JSON=$(curl -s -X POST "$BASE_URL/run" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"seed\":$SEED, \"run_id\":\"$RUN_ID-order\", \"module\":\"exchange\", \"action\":\"place_order\", \"payload\":{\"owner_address\":\"$ACCOUNT_ID\", \"side\":\"BUY\", \"asset_in\":\"NYXT\", \"asset_out\":\"ECHO\", \"amount\":100, \"price\":1}}")
echo "$ORDER_JSON" > "$ARTIFACTS_DIR/order_res.json"

if [[ "$ORDER_JSON" != *"\"status\":\"complete\""* ]]; then
    echo "❌ Order placement failed."
    exit 1
fi
echo "✅ Order Placed."

# 7. Send Chat Message
echo "💬 Sending Chat Message (E2EE Sim)..."
ENCRYPTED_BODY="{\"ciphertext\":\"dGhpcyBpcyBhIHJlYWwgZW5jcnlwdGVkIG1lc3NhZ2U=\", \"iv\":\"YWJjZGVmZ2hpamtsbW5vcA==\", \"tag\":\"MTIzNDU2Nzg5MDEyMzQ1Ng==\"}"
CHAT_JSON=$(curl -s -X POST "$BASE_URL/run" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"seed\":$SEED, \"run_id\":\"$RUN_ID-chat\", \"module\":\"chat\", \"action\":\"message_event\", \"payload\":{\"channel\":\"lobby\", \"message\":$(echo $ENCRYPTED_BODY | python3 -c 'import sys, json; print(json.dumps(sys.stdin.read().strip()))')}}")
echo "$CHAT_JSON" > "$ARTIFACTS_DIR/chat_res.json"

if [[ "$CHAT_JSON" != *"\"status\":\"complete\""* ]]; then
    echo "❌ Chat message failed."
    exit 1
fi
echo "✅ Chat Message Sent."

# 8. Verify Evidence
echo "📜 Verifying Evidence Chain..."
EVIDENCE_JSON=$(curl -s "$BASE_URL/evidence?run_id=$RUN_ID-chat")
if [[ "$EVIDENCE_JSON" != *"\"replay_ok\":true"* ]]; then
    echo "❌ Evidence verification failed: $EVIDENCE_JSON"
    exit 1
fi
echo "✅ Evidence Chain Verified."

echo "🎉 ALL VERIFICATIONS PASSED!"
echo "Artifacts saved to $ARTIFACTS_DIR"
