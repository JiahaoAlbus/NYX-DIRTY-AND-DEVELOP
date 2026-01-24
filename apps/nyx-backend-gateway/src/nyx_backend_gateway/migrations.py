from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 1


def apply_migrations(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)"
    )
    cursor.execute(
        "SELECT value FROM meta WHERE key = 'schema_version'"
    )
    row = cursor.fetchone()
    if row is None:
        cursor.execute(
            "INSERT INTO meta (key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS evidence_runs (
            run_id TEXT PRIMARY KEY,
            module TEXT NOT NULL,
            action TEXT NOT NULL,
            seed INTEGER NOT NULL,
            state_hash TEXT NOT NULL,
            receipt_hashes TEXT NOT NULL,
            replay_ok INTEGER NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            side TEXT NOT NULL,
            amount INTEGER NOT NULL,
            price INTEGER NOT NULL,
            asset_in TEXT NOT NULL,
            asset_out TEXT NOT NULL,
            run_id TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS trades (
            trade_id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            amount INTEGER NOT NULL,
            price INTEGER NOT NULL,
            run_id TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            message_id TEXT PRIMARY KEY,
            channel TEXT NOT NULL,
            body TEXT NOT NULL,
            run_id TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS listings (
            listing_id TEXT PRIMARY KEY,
            sku TEXT NOT NULL,
            title TEXT NOT NULL,
            price INTEGER NOT NULL,
            run_id TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS purchases (
            purchase_id TEXT PRIMARY KEY,
            listing_id TEXT NOT NULL,
            qty INTEGER NOT NULL,
            run_id TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS receipts (
            receipt_id TEXT PRIMARY KEY,
            module TEXT NOT NULL,
            action TEXT NOT NULL,
            state_hash TEXT NOT NULL,
            receipt_hashes TEXT NOT NULL,
            replay_ok INTEGER NOT NULL,
            run_id TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
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
        """
    )
    conn.commit()
