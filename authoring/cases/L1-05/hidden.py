import random


@check("functional.asciiCaseInsensitive")
def ascii_case_insensitive():
    from search import matches

    records = ["Mixed RECORD", "plain", "mixed-2", "MIXED"]
    return matches("mixed", records) == ["Mixed RECORD", "mixed-2", "MIXED"] and matches("PLAIN", records) == ["plain"]


@check("boundary.randomizedQueries")
def randomized_queries():
    from search import matches

    rng = random.Random(20260911)
    alphabet = "abcAB-1 "
    for _ in range(500):
        records = ["".join(rng.choice(alphabet) for _ in range(rng.randint(0, 8))) for _ in range(rng.randint(0, 8))]
        query = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 3)))
        expected = [record for record in records if query.lower() in record.lower()]
        if matches(query, records) != expected:
            return False, f"matches({query!r}, {records!r}) returned {matches(query, records)!r}"
    return True


@check("boundary.emptyQueryAndNoMatch")
def empty_and_no_match():
    from search import matches

    return matches("", ["a", "A"]) == [] and matches("zzz", ["a", "Zz"]) == [] and matches("x", []) == []


@check("regression.orderAndIdentityPreserved")
def order_and_identity():
    from search import matches

    records = ["Beta", "alpha", "ALPHA-2", "gamma"]
    result = matches("ALPHA", records)
    return result == ["alpha", "ALPHA-2"] and records == ["Beta", "alpha", "ALPHA-2", "gamma"]
