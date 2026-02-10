from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 1


def apply_migrations(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
    cursor.execute("SELECT value FROM meta WHERE key = 'schema_version'")
    row = cursor.fetchone()
    if row is None:
        cursor.execute(
            "INSERT INTO meta (key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence_runs (
            run_id TEXT PRIMARY KEY,
            module TEXT NOT NULL,
            action TEXT NOT NULL,
            seed INTEGER NOT NULL,
            state_hash TEXT NOT NULL,
            receipt_hashes TEXT NOT NULL,
            replay_ok INTEGER NOT NULL
        )
        """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            owner_address TEXT NOT NULL DEFAULT '0x0',
            side TEXT NOT NULL,
            amount INTEGER NOT NULL,
            price INTEGER NOT NULL,
            asset_in TEXT NOT NULL,
            asset_out TEXT NOT NULL,
            run_id TEXT NOT NULL
        )
        """)
    # Simple migration for owner_address
    cursor.execute("PRAGMA table_info(orders)")
    order_columns = [row[1] for row in cursor.fetchall()]
    if "owner_address" not in order_columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN owner_address TEXT NOT NULL DEFAULT '0x0'")
    if "status" not in order_columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN status TEXT NOT NULL DEFAULT 'open'")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            trade_id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            amount INTEGER NOT NULL,
            price INTEGER NOT NULL,
            run_id TEXT NOT NULL
        )
        """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id TEXT PRIMARY KEY,
            channel TEXT NOT NULL,
            sender_account_id TEXT NOT NULL DEFAULT '',
            body TEXT NOT NULL,
            run_id TEXT NOT NULL
        )
        """)
    cursor.execute("PRAGMA table_info(messages)")
    msg_columns = [row[1] for row in cursor.fetchall()]
    if "sender_account_id" not in msg_columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN sender_account_id TEXT NOT NULL DEFAULT ''")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portal_accounts (
            account_id TEXT PRIMARY KEY,
            handle TEXT UNIQUE NOT NULL,
            public_key TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            status TEXT NOT NULL,
            bio TEXT
        )
        """)
    # Check if bio column exists, if not add it (simple migration for existing db)
    cursor.execute("PRAGMA table_info(portal_accounts)")
    columns = [row[1] for row in cursor.fetchall()]
    if "bio" not in columns:
        cursor.execute("ALTER TABLE portal_accounts ADD COLUMN bio TEXT")
    if "wallet_address" not in columns:
        cursor.execute("ALTER TABLE portal_accounts ADD COLUMN wallet_address TEXT")
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_portal_accounts_wallet_address ON portal_accounts(wallet_address)"
    )
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portal_challenges (
            account_id TEXT NOT NULL,
            nonce TEXT NOT NULL,
            expires_at INTEGER NOT NULL,
            used INTEGER NOT NULL,
            PRIMARY KEY (account_id, nonce)
        )
        """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portal_sessions (
            token TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            expires_at INTEGER NOT NULL
        )
        """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS e2ee_identities (
            account_id TEXT PRIMARY KEY,
            public_jwk TEXT NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_rooms (
            room_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            is_public INTEGER NOT NULL
        )
        """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            message_id TEXT PRIMARY KEY,
            room_id TEXT NOT NULL,
            sender_account_id TEXT NOT NULL,
            body TEXT NOT NULL,
            seq INTEGER NOT NULL,
            prev_digest TEXT NOT NULL,
            msg_digest TEXT NOT NULL,
            chain_head TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
        """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            listing_id TEXT PRIMARY KEY,
            publisher_id TEXT NOT NULL DEFAULT 'unknown',
            sku TEXT NOT NULL,
            title TEXT NOT NULL,
            price INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            run_id TEXT NOT NULL
        )
        """)
    # Simple migration for listings
    cursor.execute("PRAGMA table_info(listings)")
    listing_columns = [row[1] for row in cursor.fetchall()]
    if "publisher_id" not in listing_columns:
        cursor.execute("ALTER TABLE listings ADD COLUMN publisher_id TEXT NOT NULL DEFAULT 'unknown'")
    if "status" not in listing_columns:
        cursor.execute("ALTER TABLE listings ADD COLUMN status TEXT NOT NULL DEFAULT 'active'")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            purchase_id TEXT PRIMARY KEY,
            listing_id TEXT NOT NULL,
            buyer_id TEXT NOT NULL DEFAULT 'unknown',
            qty INTEGER NOT NULL,
            run_id TEXT NOT NULL
        )
        """)
    # Simple migration for purchases
    cursor.execute("PRAGMA table_info(purchases)")
    purchase_columns = [row[1] for row in cursor.fetchall()]
    if "buyer_id" not in purchase_columns:
        cursor.execute("ALTER TABLE purchases ADD COLUMN buyer_id TEXT NOT NULL DEFAULT 'unknown'")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            receipt_id TEXT PRIMARY KEY,
            module TEXT NOT NULL,
            action TEXT NOT NULL,
            state_hash TEXT NOT NULL,
            receipt_hashes TEXT NOT NULL,
            replay_ok INTEGER NOT NULL,
            run_id TEXT NOT NULL
        )
        """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fee_ledger (
            fee_id TEXT PRIMARY KEY,
            module TEXT NOT NULL,
            action TEXT NOT NULL,
            protocol_fee_total INTEGER NOT NULL,
            platform_fee_amount INTEGER NOT NULL,
            total_paid INTEGER NOT NULL,
            fee_address TEXT NOT NULL,
            run_id TEXT NOT NULL
        )
        """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wallet_accounts (
            address TEXT NOT NULL,
            asset_id TEXT NOT NULL DEFAULT 'NYXT',
            balance INTEGER NOT NULL,
            PRIMARY KEY (address, asset_id)
        )
        """)
    # Migration for asset_id
    cursor.execute("PRAGMA table_info(wallet_accounts)")
    wallet_columns = [row[1] for row in cursor.fetchall()]
    if "asset_id" not in wallet_columns:
        # Move existing balances to NYXT
        cursor.execute(
            "CREATE TABLE wallet_accounts_new (address TEXT NOT NULL, asset_id TEXT NOT NULL DEFAULT 'NYXT', balance INTEGER NOT NULL, PRIMARY KEY (address, asset_id))"
        )
        cursor.execute(
            "INSERT INTO wallet_accounts_new (address, balance) SELECT address, balance FROM wallet_accounts"
        )
        cursor.execute("DROP TABLE wallet_accounts")
        cursor.execute("ALTER TABLE wallet_accounts_new RENAME TO wallet_accounts")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wallet_transfers (
            transfer_id TEXT PRIMARY KEY,
            from_address TEXT NOT NULL,
            to_address TEXT NOT NULL,
            asset_id TEXT NOT NULL DEFAULT 'NYXT',
            amount INTEGER NOT NULL,
            fee_total INTEGER NOT NULL,
            treasury_address TEXT NOT NULL,
            run_id TEXT NOT NULL
        )
        """)
    # Migration for asset_id in wallet_transfers
    cursor.execute("PRAGMA table_info(wallet_transfers)")
    transfer_columns = [row[1] for row in cursor.fetchall()]
    if "asset_id" not in transfer_columns:
        cursor.execute("ALTER TABLE wallet_transfers ADD COLUMN asset_id TEXT NOT NULL DEFAULT 'NYXT'")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faucet_claims (
            claim_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            address TEXT NOT NULL,
            asset_id TEXT NOT NULL,
            amount INTEGER NOT NULL,
            ip TEXT NOT NULL DEFAULT 'unknown',
            created_at INTEGER NOT NULL,
            run_id TEXT NOT NULL
        )
        """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS airdrop_claims (
            claim_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            reward INTEGER NOT NULL,
            created_at INTEGER NOT NULL,
            run_id TEXT NOT NULL,
            UNIQUE (account_id, task_id)
        )
        """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entertainment_items (
            item_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            category TEXT NOT NULL
        )
        """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entertainment_events (
            event_id TEXT PRIMARY KEY,
            item_id TEXT NOT NULL,
            mode TEXT NOT NULL,
            step INTEGER NOT NULL,
            run_id TEXT NOT NULL
        )
        """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS web2_guard_requests (
            request_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            run_id TEXT NOT NULL,
            url TEXT NOT NULL,
            method TEXT NOT NULL,
            request_hash TEXT NOT NULL,
            response_hash TEXT NOT NULL,
            response_status INTEGER NOT NULL,
            response_size INTEGER NOT NULL,
            response_truncated INTEGER NOT NULL,
            body_size INTEGER NOT NULL,
            header_names TEXT NOT NULL,
            sealed_request TEXT,
            created_at INTEGER NOT NULL
        )
        """)
    conn.commit()
