import unittest

from opsdesk.api.tools import describe_tools, invoke_tool


def recorder(**arguments):
    return arguments


class ToolApiTest(unittest.TestCase):
    def test_arguments_reach_the_handler(self):
        received = invoke_tool("send_notification", {"channel": "email", "message": "disk almost full"}, recorder)

        self.assertEqual("email", received["channel"])
        self.assertEqual("disk almost full", received["message"])
        self.assertNotIn("urgent", received)

    def test_booleans_survive_the_wire_format(self):
        received = invoke_tool("send_notification", {"channel": "sms", "message": "down", "urgent": True}, recorder)

        self.assertIs(True, received["urgent"])

    def test_required_arguments_are_enforced(self):
        with self.assertRaises(ValueError):
            invoke_tool("send_notification", {"channel": "email"}, recorder)

    def test_argument_types_are_enforced(self):
        with self.assertRaises(ValueError):
            invoke_tool("send_notification", {"channel": "email", "message": "x", "urgent": "yes"}, recorder)

    def test_unknown_arguments_and_tools_are_rejected(self):
        with self.assertRaises(ValueError):
            invoke_tool("send_notification", {"channel": "email", "message": "x", "colour": "red"}, recorder)
        with self.assertRaises(ValueError):
            invoke_tool("reboot_everything", {}, recorder)

    def test_tools_are_described(self):
        (tool,) = describe_tools()

        self.assertEqual("send_notification", tool["name"])
        self.assertEqual(["channel", "message"], tool["parameters"]["required"])
        self.assertEqual("string", tool["parameters"]["properties"]["channel"]["type"])
        self.assertEqual("boolean", tool["parameters"]["properties"]["urgent"]["type"])


if __name__ == "__main__":
    unittest.main()
