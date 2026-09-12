import random


def _expected(items, page, size):
    start = (page - 1) * size
    return items[start:start + size]


@check("functional.fullPages")
def full_pages():
    from pagination import PageWindow

    items = [str(index) for index in range(12)]
    return PageWindow.slice(items, 1, 4) == ["0", "1", "2", "3"] and PageWindow.slice(items, 3, 4) == ["8", "9", "10", "11"]


@check("boundary.lastPartialPage")
def last_partial_page():
    from pagination import PageWindow

    got = PageWindow.slice([str(index) for index in range(10)], 3, 4)
    return got == ["8", "9"], f"10 items, page 3, size 4 returned {got}"


@check("boundary.beyondEndAndEmptyInput")
def beyond_end():
    from pagination import PageWindow

    return (
        PageWindow.slice(["a", "b"], 2, 2) == []
        and PageWindow.slice(["a", "b"], 9, 5) == []
        and PageWindow.slice([], 1, 3) == []
        and PageWindow.slice(["x"], 1, 4) == ["x"]
    )


@check("boundary.randomizedWindows")
def randomized_windows():
    from pagination import PageWindow

    rng = random.Random(20260911)
    for _ in range(500):
        items = [f"i{index}" for index in range(rng.randint(0, 30))]
        page, size = rng.randint(1, 9), rng.randint(1, 7)
        got = PageWindow.slice(list(items), page, size)
        if got != _expected(items, page, size):
            return False, f"{len(items)} items, page {page}, size {size} returned {got}"
    return True


@check("regression.argumentValidation")
def argument_validation():
    from pagination import PageWindow

    for arguments in ((["a"], 0, 3), (["a"], -1, 3), (["a"], 1, 0), (["a"], 1, -2)):
        try:
            PageWindow.slice(*arguments)
        except ValueError:
            continue
        return False, f"slice{arguments} did not raise ValueError"
    return True


@check("regression.pageCountUnchanged")
def page_count_unchanged():
    from pagination import page_count

    return all(page_count(total, size) == (0 if total <= 0 else -(-total // size)) for total in range(-2, 40) for size in range(1, 9))
