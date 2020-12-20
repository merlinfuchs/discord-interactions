__all__ = (
    "iterable_get",
)


def iterable_get(iterable, **kwargs):
    for item in iterable:
        for key, value in kwargs.items():
            if getattr(item, key) != value:
                break

        else:
            return item

    return None
