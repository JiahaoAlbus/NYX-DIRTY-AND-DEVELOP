class LedgerError(ValueError):
    pass


class ValidationError(LedgerError):
    pass


class DoubleSpendError(LedgerError):
    pass
