class RouterError(ValueError):
    pass


class ValidationError(RouterError):
    pass


class ReplayError(RouterError):
    pass
