from .command import *


__all__ = (
    "Module",
)


class Module:
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def command(_callable=None, **kwargs):
        if _callable is None:
            def _predicate(_callable):
                return make_command(Command, _callable, **kwargs)

            return _predicate

        return make_command(Command, _callable, **kwargs)

    @property
    def commands(self):
        for name in dir(self):
            attr = getattr(self, name)
            if isinstance(attr, Command):
                attr.bind(self)
                yield attr
