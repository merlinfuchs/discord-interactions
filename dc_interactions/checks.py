import inspect

from .errors import *


__all__ = (
    "Check",
)


class Check:
    def __init__(self, callable, next=None):
        self.callable = callable
        self.next = next

    def __call__(self, next):
        self.next = next
        return self

    async def run(self, ctx, *args):
        result = self.callable(ctx, *args)
        if inspect.isawaitable(result):
            result = await result

        return result
