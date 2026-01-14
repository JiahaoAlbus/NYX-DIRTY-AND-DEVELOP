from __future__ import annotations

from e2e_private_transfer.trace import TransferTrace


__all__ = ["Summary", "TransferTrace", "run_private_transfer", "replay_and_verify"]


def run_private_transfer(seed: int = 123):
    from e2e_private_transfer.pipeline import run_private_transfer as _run

    return _run(seed=seed)


def replay_and_verify(trace: TransferTrace) -> bool:
    from e2e_private_transfer.replay import replay_and_verify as _replay

    return _replay(trace)


def Summary(*args, **kwargs):
    from e2e_private_transfer.pipeline import Summary as _Summary

    return _Summary(*args, **kwargs)
