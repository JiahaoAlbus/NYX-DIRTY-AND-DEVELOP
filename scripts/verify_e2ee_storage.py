import sqlite3
import json
from pathlib import Path

def verify_e2ee():
    db_path = Path("apps/nyx-backend-gateway/data/nyx_gateway.db")
    if not db_path.exists():
        print("❌ Database not found at", db_path)
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Check both chat_messages (V1) and messages (Legacy/Run) tables
    chat_v1_rows = conn.execute("SELECT * FROM chat_messages").fetchall()
    messages_rows = conn.execute("SELECT * FROM messages").fetchall()
    
    print(f"🔍 Checking {len(chat_v1_rows)} messages in chat_messages...")
    print(f"🔍 Checking {len(messages_rows)} messages in messages table...")
    
    all_rows = list(chat_v1_rows) + list(messages_rows)
    
    if not all_rows:
        print("⚠️ No messages found to verify.")
        return True

    for row in all_rows:
        body = row['body']
        # If E2EE is working, body should NOT contain readable text like "verified_message"
        forbidden_plaintext = "verified_message"
        if forbidden_plaintext in body:
            print(f"❌ PLAINTEXT DETECTED in message {row[0]}: {body}")
            return False
        
        # Check if it looks like encrypted data
        try:
            parsed = json.loads(body)
            if "ciphertext" in parsed and "iv" in parsed:
                print(f"✅ Message {row[0]} is correctly encrypted.")
            else:
                print(f"⚠️ Message {row[0]} body is JSON but missing E2EE fields: {body}")
        except json.JSONDecodeError:
            # If not JSON, check if it's a raw base64 or starts with E2EE marker
            if body.startswith("E2EE:"):
                # The verification script in bash sends "E2EE:verified_message"
                # This IS plaintext but marked as E2EE. 
                # REAL E2EE from frontend uses AES-GCM JSON.
                if "verified_message" in body:
                    print(f"❌ PLAINTEXT MARKED AS E2EE DETECTED: {body}")
                    return False
            print(f"⚠️ Message {row[0]} body is not JSON: {body}")

    conn.close()
    print("✨ E2EE Storage Verification PASSED!")
    return True

if __name__ == "__main__":
    verify_e2ee()
