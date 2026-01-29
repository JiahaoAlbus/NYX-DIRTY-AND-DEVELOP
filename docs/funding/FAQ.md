# NYX FAQ

## General

**Q: Is NYX a blockchain?**
A: No. It is a deterministic portal infrastructure. It can settle to a blockchain, but it runs as a lightweight state machine optimized for user experience and evidence generation.

**Q: Why "Testnet Only"?**
A: We prioritize safety. Until the deterministic engine is fully audited and the "No Fake Data" gates are battle-tested, we will not touch real assets.

**Q: Who controls the keys?**
A: Users control their keys (Self-Custody). The Portal (NYX) only sees signed intents.

## Technical

**Q: How do you guarantee determinism in Python?**
A: We use a strict subset of Python, avoiding non-deterministic features (like `set` iteration order or system time). We use seeded RNGs and explicit state passing.

**Q: Can I run my own node?**
A: Yes. The entire backend is open source and can be run locally via `scripts/nyx_backend_dev.sh`.

**Q: What prevents the backend from censoring me?**
A: Currently, the testnet is a single sequencer. In the future, a decentralized network of sequencers will provide censorship resistance. For now, you can fork the state and run your own.

## Business

**Q: How does NYX make money?**
A: The protocol enforces a `platform_fee`. Operators (including us) earn fees for hosting portals. We also plan to offer enterprise support for "Private NYX" instances.

**Q: Why a Solo Founder?**
A: Speed and coherence. The initial vision requires tight integration across the full stack (iOS, Web, Backend, Protocol). We are expanding the team via grants and contributors.
