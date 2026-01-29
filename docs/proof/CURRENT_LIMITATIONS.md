# Current Limitations

## Purpose
To transparently document the known limitations of the current v1 testnet implementation.

## Technical Limitations

1.  **Centralized Sequencer**: The current backend runs as a single process. While deterministic, it is a single point of failure (SPOF) for availability (but not for integrity, as evidence is verifiable).
2.  **Transient State**: By default, state is stored in memory or temporary files. Restarting the backend without the same seed/history resets the world state.
3.  **Scaling**: The Python implementation is optimized for clarity and correctness, not high-frequency trading (HFT) throughput.
4.  **Auth**: Portal authentication is basic (Challenge-Response). It does not yet support multi-factor or hardware wallet integration.
5.  **Persistence**: Long-term storage adapters (e.g., Postgres/S3) are defined in interfaces but the default testnet uses filesystem storage.

## Operational Limitations

1.  **No SLA**: This is a testnet. Uptime is not guaranteed.
2.  **Manual Updates**: Client updates are currently manual (git pull / TestFlight).
3.  **No Real Value**: Assets have zero monetary value.
