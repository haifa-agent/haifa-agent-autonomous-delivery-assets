import random
import re
import string

SLUG = re.compile(r"^([a-z0-9]+(-[a-z0-9]+)*)?$")
SEPARATORS = (" ", "_", "-", " - ", "__", " & ", "--", " (", ") ", " !", "\t", " / ")


def _words(rng):
    alphabet = string.ascii_letters + string.digits
    return ["".join(rng.choice(alphabet) for _ in range(rng.randint(1, 6))) for _ in range(rng.randint(1, 5))]


@check("functional.visibleExamples")
def visible_examples():
    from slugify import slugify

    examples = {
        "Hello World": "hello-world",
        "--Edge--Cases--": "edge-cases",
        "multi___underscore   run": "multi-underscore-run",
        "Release  Notes (v2.0)!!": "release-notes-v20",
        "rock & roll": "rock-roll",
    }
    for text, expected in examples.items():
        if slugify(text) != expected:
            return False, f"slugify({text!r}) returned {slugify(text)!r}"
    return True


@check("boundary.randomizedWordJoins")
def randomized_word_joins():
    from slugify import slugify

    rng = random.Random(20260911)
    for _ in range(400):
        words = _words(rng)
        text = rng.choice(SEPARATORS) * rng.randint(0, 2)
        for index, word in enumerate(words):
            if index:
                text += "".join(rng.choice(SEPARATORS) for _ in range(rng.randint(1, 3)))
            text += word
        text += rng.choice(SEPARATORS) * rng.randint(0, 2)
        expected = "-".join(word.lower() for word in words)
        if slugify(text) != expected:
            return False, f"slugify({text!r}) returned {slugify(text)!r}, expected {expected!r}"
    return True


@check("boundary.outputAlphabet")
def output_alphabet():
    from slugify import slugify

    rng = random.Random(7)
    for _ in range(400):
        text = "".join(rng.choice(string.printable) for _ in range(rng.randint(0, 24)))
        result = slugify(text)
        if not SLUG.match(result):
            return False, f"slugify({text!r}) returned {result!r}"
    return True


@check("boundary.idempotent")
def idempotent():
    from slugify import slugify

    rng = random.Random(11)
    for _ in range(300):
        text = "".join(rng.choice(string.printable) for _ in range(rng.randint(0, 24)))
        once = slugify(text)
        if slugify(once) != once:
            return False, f"slugify is not idempotent for {text!r}"
    return True


@check("boundary.symbolsOnly")
def symbols_only():
    from slugify import slugify

    return all(slugify(text) == "" for text in ("", "   ", "!!!", "---", "_ - _", "(&)"))
