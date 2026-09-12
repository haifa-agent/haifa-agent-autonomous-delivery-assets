BASE = {"channel": "email", "message": "disk almost full"}


class _Recorder:
    def __init__(self):
        self.calls = []

    def __call__(self, **arguments):
        self.calls.append(arguments)
        return arguments


def _invoke(arguments, recorder=None):
    from opsdesk.api.tools import invoke_tool

    return invoke_tool("send_notification", arguments, recorder or _Recorder())


def _rejected(value):
    recorder = _Recorder()
    try:
        _invoke(dict(BASE, max_retries=value), recorder)
    except ValueError:
        return not recorder.calls
    return False


@check("functional.defaultAppliedAsInt")
def default_applied():
    received = _invoke(dict(BASE))
    value = received.get("max_retries")
    return value == 3 and type(value) is int, repr(received)


@check("functional.valueForwardedAsInt")
def value_forwarded():
    for value in (0, 1, 5):
        received = _invoke(dict(BASE, max_retries=value))
        if received.get("max_retries") != value or type(received.get("max_retries")) is not int:
            return False, repr(received)
    return True


@check("boundary.rangeEnforced")
def range_enforced():
    for value in (-1, 6, 100):
        if not _rejected(value):
            return False, f"max_retries={value} was not rejected before the handler"
    return True


@check("boundary.nonIntegerRejected")
def non_integer():
    for value in ("3", 2.5, "three"):
        if not _rejected(value):
            return False, f"max_retries={value!r} was not rejected before the handler"
    return True


@check("functional.parameterDescribed")
def described():
    from opsdesk.api.tools import describe_tools

    (tool,) = describe_tools()
    parameters = tool["parameters"]
    spec = parameters["properties"].get("max_retries", {})
    return (
        spec.get("type") == "integer"
        and spec.get("default") == 3
        and spec.get("minimum") == 0
        and spec.get("maximum") == 5
        and "max_retries" not in parameters["required"],
        repr(spec),
    )


@check("regression.existingParameters")
def existing_parameters():
    from opsdesk.api.tools import describe_tools

    received = _invoke(dict(BASE, urgent=True))
    for arguments in ({"channel": "email"}, dict(BASE, urgent="yes"), dict(BASE, colour="red")):
        try:
            _invoke(arguments)
            return False, f"{arguments} accepted"
        except ValueError:
            pass
    (tool,) = describe_tools()
    properties = tool["parameters"]["properties"]
    return (
        received.get("channel") == "email"
        and received.get("message") == "disk almost full"
        and received.get("urgent") is True
        and tool["parameters"]["required"] == ["channel", "message"]
        and properties["channel"]["type"] == "string"
        and properties["urgent"]["type"] == "boolean",
        repr(received),
    )
