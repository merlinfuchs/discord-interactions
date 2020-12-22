import inspect

from .errors import *


__all__ = (
    "Check",
    "has_permissions"
)


class Check:
    def __init__(self, callable):
        self.callable = callable
        self.next = None

    def __call__(self, next):
        self.next = next
        return self

    async def run(self, ctx, *args):
        result = self.callable(ctx, *args)
        if inspect.isawaitable(result):
            result = await result

        return result


def has_permissions(value: int):
    @Check
    async def _check(ctx, *_):
        permissions = int(ctx.member["permissions"])
        if (permissions & value) != value and (permissions & 8) != 8:
            raise MissingPermissions(value)

        return True

    return _check
