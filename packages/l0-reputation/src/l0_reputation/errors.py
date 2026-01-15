from __future__ import annotations


class ReputationError(ValueError):
    pass


class ValidationError(ReputationError):
    pass


class FeeBindingError(ReputationError):
    pass
