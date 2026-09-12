import ast
import inspect
import os
import random
import string
import sys

BASELINE_PUBLIC = {"accounts.py": {"RegistrationError", "ACCOUNTS", "register"}, "signup.py": {"handle_signup"}}
INVALID = ("nope", "a@b", "@b.com", "a b@c.com", "a@b..com", "a@.com", "a@b.c", "a@@b.com", "a@b.com.", "a@b.c0m", "a@b_c.com")
VALID = ("user.name+tag@example.co.uk", "x@y.io", "first-last@sub-domain.example.org", "o'neil@a1.b2.info")


def _valid(address):
    if address.count("@") != 1:
        return False
    local, domain = address.split("@")
    if not local or any(character.isspace() for character in local):
        return False
    labels = domain.split(".")
    allowed = set(string.ascii_letters + string.digits + "-")
    if len(labels) < 2 or any(not label or set(label) - allowed for label in labels):
        return False
    return len(labels[-1]) >= 2 and all(character in string.ascii_letters for character in labels[-1])


def _outcome(email):
    from accounts import ACCOUNTS, RegistrationError, register

    ACCOUNTS.clear()
    try:
        account = register(email)
    except RegistrationError as error:
        return ("rejected", error.code, list(ACCOUNTS))
    return ("stored", account, list(ACCOUNTS))


def _public_names(filename):
    tree = ast.parse(open(os.path.join(WORKSPACE, filename), encoding="utf-8").read())
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(target.id for target in node.targets if isinstance(target, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return {name for name in names if not name.startswith("_")}


@check("functional.malformedRejectedWithCode")
def malformed_rejected():
    for email in INVALID:
        outcome = _outcome(email)
        if outcome != ("rejected", "invalid_email", []):
            return False, f"{email!r}: {outcome}"
    return True


@check("functional.validAddressesStored")
def valid_stored():
    for email in VALID:
        outcome = _outcome(email)
        if outcome != ("stored", {"email": email}, [{"email": email}]):
            return False, f"{email!r}: {outcome}"
    return True


@check("functional.signupAnswers400")
def signup_answers():
    from accounts import ACCOUNTS
    from signup import handle_signup

    ACCOUNTS.clear()
    rejected = handle_signup({"email": "a@b"})
    missing = handle_signup({})
    accepted = handle_signup({"email": "ok@example.org"})
    return (
        rejected == (400, {"error": "invalid_email"})
        and missing == (400, {"error": "invalid_email"})
        and accepted == (201, {"email": "ok@example.org"}),
        f"{rejected} {missing} {accepted}",
    )


@check("boundary.randomizedAddresses")
def randomized():
    rng = random.Random(20260911)
    pieces_local = ["ab", "x.y", "+t", "", " ", "q_z", "\t", "é"]
    pieces_label = ["ab", "c1", "d-e", "", "g", "HI", "_x", "9"]
    for _ in range(600):
        local = "".join(rng.choice(pieces_local) for _ in range(rng.randint(0, 2)))
        labels = [rng.choice(pieces_label) for _ in range(rng.randint(1, 3))]
        address = local + "@" * rng.choice((0, 1, 1, 1, 2)) + ".".join(labels)
        outcome = _outcome(address)
        expected_valid = _valid(address)
        if expected_valid and outcome[0] != "stored":
            return False, f"valid {address!r} rejected"
        if not expected_valid and outcome[:2] != ("rejected", "invalid_email"):
            return False, f"invalid {address!r} -> {outcome[:2]}"
    return True


@check("regression.duplicateStillReported")
def duplicate_reported():
    from accounts import ACCOUNTS, RegistrationError, register

    ACCOUNTS.clear()
    register("dup@example.com")
    try:
        register("dup@example.com")
    except RegistrationError as error:
        return error.code == "duplicate_email" and isinstance(error, ValueError) and len(ACCOUNTS) == 1
    return False, "duplicate accepted"


@check("constraint.publicApiFrozen")
def public_api_frozen():
    for filename, baseline in BASELINE_PUBLIC.items():
        names = _public_names(filename)
        if names != baseline:
            return False, f"{filename} public names {sorted(names)} != {sorted(baseline)}"
    for filename in BASELINE_PUBLIC:
        tree = ast.parse(open(os.path.join(WORKSPACE, filename), encoding="utf-8").read())
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                modules = [node.module]
            for module in modules:
                top = module.split(".")[0]
                if top not in sys.stdlib_module_names and top not in {"accounts", "signup", "__future__"}:
                    return False, f"{filename} imports third-party module {module}"
    return True


@check("constraint.registerSignatureKept")
def signature_kept():
    from accounts import register

    parameters = list(inspect.signature(register).parameters.values())
    return (
        [parameter.name for parameter in parameters] == ["email"]
        and parameters[0].default is inspect.Parameter.empty
        and parameters[0].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD,
        str(inspect.signature(register)),
    )
