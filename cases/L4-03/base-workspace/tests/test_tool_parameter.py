import unittest

from adapter_dto import to_wire
from runtime_binding import invoke
from tool_definition import SEND_NOTIFICATION
from validator import validate


def recorder(**arguments):
    return dict(arguments)


class ToolParameterTest(unittest.TestCase):
    def test_parameter_is_declared(self):
        spec = SEND_NOTIFICATION["parameters"]["max_retries"]

        self.assertEqual(3, spec["default"])
        self.assertEqual(0, spec["minimum"])
        self.assertEqual(5, spec["maximum"])

    def test_default_is_applied(self):
        self.assertEqual({"channel": "email", "max_retries": 3}, validate({"channel": "email"}))

    def test_value_is_forwarded_to_the_handler(self):
        self.assertEqual({"channel": "email", "max_retries": 5}, invoke({"channel": "email", "max_retries": 5}, recorder))

    def test_out_of_range_is_rejected(self):
        for invalid in (-1, 6):
            with self.assertRaises(ValueError):
                validate({"channel": "email", "max_retries": invalid})

    def test_required_argument_is_still_enforced(self):
        with self.assertRaises(ValueError):
            validate({})

    def test_wire_payload_contains_the_parameter(self):
        self.assertEqual({"channel": "email", "max_retries": 2}, to_wire({"channel": "email", "max_retries": 2})["arguments"])


if __name__ == "__main__":
    unittest.main()