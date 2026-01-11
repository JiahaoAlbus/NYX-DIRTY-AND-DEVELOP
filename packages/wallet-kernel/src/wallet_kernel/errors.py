class KernelError(Exception):
    pass


class ValidationError(KernelError):
    pass


class PolicyError(KernelError):
    pass


class ProofError(KernelError):
    pass


class KeyStoreError(KernelError):
    pass


class SigningError(KernelError):
    pass
