class InteractionError(Exception):
    pass


class OutOfSync(InteractionError):
    pass


class CheckFailed(InteractionError):
    pass


class MissingPermissions(CheckFailed):
    def __init__(self, missing):
        super().__init__(missing)
        self.missing = missing


class ConverterFailed(InteractionError):
    def __init__(self, value):
        super().__init__(value)
        self.value = value


class NotASnowflake(ConverterFailed):
    pass
