class InteractionError(Exception):
    pass


class OutOfSync(InteractionError):
    pass


class CheckFailed(InteractionError):
    pass


class ConverterFailed(InteractionError):
    def __init__(self, value):
        self.value = value


class NotASnowflake(ConverterFailed):
    pass
